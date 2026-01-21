#!/usr/bin/env python3
"""
Tiered Entity Resolution: SafeGraph Brands → PAW Companies

Three-tier matching strategy:
  Tier 1: Direct ticker matching (highest confidence)
  Tier 2: Parent brand inheritance (high confidence)
  Tier 3: Semantic + Jaro-Winkler fuzzy matching (medium confidence)

For Tier 3, prioritizes PAW companies with tickers/gvkeys.

Usage: python 20_tiered_entity_resolution.py
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import jellyfish

if 'OPENAI_API_KEY' not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable not set")

from openai import OpenAI

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
INPUT_DIR = PROJECT_DIR / "inputs"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "entity_resolution"
CACHE_DIR = OUTPUT_DIR / "embedding_cache"  # Use existing cache with 535K company embeddings

SAFEGRAPH_BRANDS = INPUT_DIR / "safegraph_brand_info" / "brand-info-spend-patterns.parquet"
PAW_COMPANIES = OUTPUT_DIR / "paw_companies_for_matching.parquet"

# Use text-embedding-3-small to match existing cached embeddings
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 2000
TOP_K = 20
TIER3_THRESHOLD = 0.75


def tokenize(s: str) -> set:
    """Tokenize string into lowercase word set."""
    return set(s.lower().split())


def token_jaccard(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    tokens_a = tokenize(a)
    tokens_b = tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


def contains_match(a: str, b: str) -> bool:
    """Check if one string is contained in the other."""
    a_lower = a.lower()
    b_lower = b.lower()
    return a_lower in b_lower or b_lower in a_lower


def normalize_name(name: str) -> str:
    """Normalize company/brand name for matching."""
    if not isinstance(name, str):
        return ""
    name = name.strip()[:500]
    name = ''.join(c if c.isprintable() or c in ' \t' else ' ' for c in name)
    return ' '.join(name.split())


def get_embeddings_batch(client: OpenAI, texts: list) -> list:
    """Get embeddings for a batch of texts."""
    response = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in response.data]


def load_cached_embeddings(cache_file: Path, expected_count: int) -> np.ndarray:
    """Load embeddings from cache file (supports both .npy and .json formats)."""
    npy_file = cache_file.with_suffix('.npy')
    json_file = cache_file.with_suffix('.json')

    # Try numpy format first (faster)
    if npy_file.exists():
        print(f"    Loading from numpy cache: {npy_file.name}")
        data = np.load(npy_file)
        if len(data) == expected_count:
            return data.astype(np.float32)
        print(f"    Cache size mismatch ({len(data)} vs {expected_count})")

    # Try JSON format (existing cache)
    if json_file.exists():
        print(f"    Loading from JSON cache: {json_file.name}")
        with open(json_file, 'r') as f:
            data = json.load(f)
        if len(data) == expected_count:
            print(f"    Loaded {len(data):,} embeddings, converting to numpy...")
            return np.array(data, dtype=np.float32)
        print(f"    Cache size mismatch ({len(data)} vs {expected_count})")

    return None


def generate_embeddings(client: OpenAI, names: list, cache_file: Path, desc: str) -> np.ndarray:
    """Generate embeddings with caching. Checks for existing cache first."""
    print(f"  Processing embeddings for {len(names):,} {desc}...")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Check for existing cache
    cached = load_cached_embeddings(cache_file, len(names))
    if cached is not None:
        print(f"    Using cached embeddings ({len(cached):,} x {cached.shape[1]} dimensions)")
        return cached

    print(f"    No valid cache found, generating new embeddings...")
    all_embeddings = []
    total_batches = (len(names) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(names), BATCH_SIZE):
        batch = names[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        if batch_num % 5 == 0 or batch_num == total_batches:
            print(f"    Batch {batch_num}/{total_batches}...")

        max_retries = 5
        for attempt in range(max_retries):
            try:
                embeddings = get_embeddings_batch(client, batch)
                all_embeddings.extend(embeddings)
                time.sleep(0.1)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5
                    print(f"    Error on batch {batch_num}: {e}, retry {attempt + 1}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"    Failed batch {batch_num} after {max_retries} attempts: {e}")
                    raise

    embeddings_array = np.array(all_embeddings, dtype=np.float32)

    # Save as numpy for future use
    npy_file = cache_file.with_suffix('.npy')
    np.save(npy_file, embeddings_array)
    print(f"    Cached to {npy_file.name}")

    return embeddings_array


def tier1_ticker_matching(sg: pd.DataFrame, paw: pd.DataFrame) -> pd.DataFrame:
    """Tier 1: Direct ticker matching."""
    print("\n" + "=" * 70)
    print("TIER 1: Direct Ticker Matching")
    print("=" * 70)

    sg_with_ticker = sg[sg['STOCK_SYMBOL'].notna() & (sg['STOCK_SYMBOL'] != '') & (sg['STOCK_SYMBOL'] != 'None')].copy()
    sg_with_ticker['ticker_upper'] = sg_with_ticker['STOCK_SYMBOL'].str.upper().str.strip()

    paw_with_ticker = paw[paw['ticker'].notna() & (paw['ticker'] != '') & (paw['ticker'] != 'None')].copy()
    paw_with_ticker['ticker_upper'] = paw_with_ticker['ticker'].str.upper().str.strip()

    paw_tickers = paw_with_ticker.drop_duplicates('ticker_upper')[
        ['ticker_upper', 'rcid', 'company_name', 'gvkey', 'final_parent_company', 'final_parent_company_rcid']
    ]

    print(f"  SafeGraph brands with tickers: {len(sg_with_ticker)}")
    print(f"  PAW companies with unique tickers: {len(paw_tickers)}")

    matches = sg_with_ticker.merge(paw_tickers, on='ticker_upper', how='inner')

    tier1 = matches[[
        'SAFEGRAPH_BRAND_ID', 'BRAND_NAME', 'STOCK_SYMBOL', 'NAICS_CODE',
        'rcid', 'company_name', 'gvkey', 'final_parent_company', 'final_parent_company_rcid'
    ]].copy()
    tier1['match_tier'] = 1
    tier1['match_method'] = 'ticker'
    tier1['confidence'] = 1.0

    print(f"  Tier 1 matches: {len(tier1)} brands")

    return tier1


def tier2_parent_inheritance(sg: pd.DataFrame, tier1: pd.DataFrame) -> pd.DataFrame:
    """Tier 2: Parent brand inheritance."""
    print("\n" + "=" * 70)
    print("TIER 2: Parent Brand Inheritance")
    print("=" * 70)

    tier1_brand_ids = set(tier1['SAFEGRAPH_BRAND_ID'].unique())

    sg_with_parent = sg[
        sg['PARENT_SAFEGRAPH_BRAND_ID'].notna() &
        (sg['PARENT_SAFEGRAPH_BRAND_ID'] != '') &
        (~sg['SAFEGRAPH_BRAND_ID'].isin(tier1_brand_ids))
    ].copy()

    print(f"  Brands with parent (not in Tier 1): {len(sg_with_parent)}")

    tier1_parent_map = tier1.set_index('SAFEGRAPH_BRAND_ID')[
        ['rcid', 'company_name', 'gvkey', 'final_parent_company', 'final_parent_company_rcid']
    ].to_dict('index')

    tier2_records = []
    for _, row in sg_with_parent.iterrows():
        parent_id = row['PARENT_SAFEGRAPH_BRAND_ID']
        if parent_id in tier1_parent_map:
            parent_match = tier1_parent_map[parent_id]
            tier2_records.append({
                'SAFEGRAPH_BRAND_ID': row['SAFEGRAPH_BRAND_ID'],
                'BRAND_NAME': row['BRAND_NAME'],
                'STOCK_SYMBOL': row['STOCK_SYMBOL'],
                'NAICS_CODE': row['NAICS_CODE'],
                'rcid': parent_match['rcid'],
                'company_name': parent_match['company_name'],
                'gvkey': parent_match['gvkey'],
                'final_parent_company': parent_match['final_parent_company'],
                'final_parent_company_rcid': parent_match['final_parent_company_rcid'],
                'match_tier': 2,
                'match_method': 'parent_inheritance',
                'confidence': 0.95,
                'parent_brand_id': parent_id
            })

    tier2 = pd.DataFrame(tier2_records)
    print(f"  Tier 2 matches: {len(tier2)} brands")

    return tier2


def tier3_fuzzy_matching(sg: pd.DataFrame, paw: pd.DataFrame,
                          matched_brand_ids: set, client: OpenAI) -> pd.DataFrame:
    """Tier 3: Semantic + Jaro-Winkler fuzzy matching."""
    print("\n" + "=" * 70)
    print("TIER 3: Semantic + Jaro-Winkler Fuzzy Matching")
    print("=" * 70)

    sg_unmatched = sg[~sg['SAFEGRAPH_BRAND_ID'].isin(matched_brand_ids)].copy()
    print(f"  Unmatched brands to process: {len(sg_unmatched)}")

    sg_unmatched['brand_name_clean'] = sg_unmatched['BRAND_NAME'].apply(normalize_name)
    sg_unmatched = sg_unmatched[sg_unmatched['brand_name_clean'] != ''].copy()

    # Match against ALL PAW companies, not just verified ones
    # PAW has employee ideology data for private companies too
    # IMPORTANT: Keep exact same order as parquet to match existing cached embeddings
    paw_all = paw.copy()
    paw_all['company_name_clean'] = paw_all['company_name'].apply(normalize_name)
    # Don't filter - keep same count as cache (535,165)

    print(f"  Total PAW companies for matching: {len(paw_all)}")

    brand_names = sg_unmatched['brand_name_clean'].tolist()
    company_names = paw_all['company_name'].tolist()  # Use original names, not normalized, for cache

    # Use existing cache file names (company_embeddings.json has 535K embeddings)
    brand_cache = CACHE_DIR / "safegraph_brand_embeddings"  # New cache for SafeGraph brands
    company_cache = CACHE_DIR / "company_embeddings"  # Existing 535K company cache

    brand_embeddings = generate_embeddings(client, brand_names, brand_cache, "SafeGraph brand names")
    company_embeddings = generate_embeddings(client, company_names, company_cache, "PAW company names")

    print("\n  Finding top-K candidates and computing features...")

    brand_norms = np.linalg.norm(brand_embeddings, axis=1, keepdims=True)
    company_norms = np.linalg.norm(company_embeddings, axis=1, keepdims=True)
    brand_normalized = brand_embeddings / (brand_norms + 1e-10)
    company_normalized = company_embeddings / (company_norms + 1e-10)

    tier3_records = []
    chunk_size = 500

    for start in range(0, len(brand_names), chunk_size):
        end = min(start + chunk_size, len(brand_names))
        if start % 2000 == 0:
            print(f"    Processing brands {start:,}-{end:,} / {len(brand_names):,}...")

        chunk = brand_normalized[start:end]
        similarities = np.dot(chunk, company_normalized.T)

        for i, sim_row in enumerate(similarities):
            brand_idx = start + i
            brand_name = brand_names[brand_idx]
            brand_row = sg_unmatched.iloc[brand_idx]

            top_k_idx = np.argpartition(sim_row, -TOP_K)[-TOP_K:]
            top_k_idx = top_k_idx[np.argsort(sim_row[top_k_idx])[::-1]]

            best_match = None
            best_score = 0

            for company_idx in top_k_idx:
                company_name = company_names[company_idx]
                cos_sim = float(sim_row[company_idx])

                jw_sim = jellyfish.jaro_winkler_similarity(brand_name.lower(), company_name.lower())
                jw_norm = jellyfish.jaro_winkler_similarity(
                    normalize_name(brand_name).lower(),
                    normalize_name(company_name).lower()
                )
                tj = token_jaccard(brand_name, company_name)
                contains = 1.0 if contains_match(brand_name, company_name) else 0.0

                combined_score = (0.4 * cos_sim + 0.3 * jw_norm + 0.2 * tj + 0.1 * contains)

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        'company_idx': company_idx,
                        'company_name': company_name,
                        'cos_sim': cos_sim,
                        'jaro_winkler': jw_sim,
                        'jaro_winkler_norm': jw_norm,
                        'token_jaccard': tj,
                        'contains_match': contains,
                        'combined_score': combined_score
                    }

            if best_match and best_match['combined_score'] >= TIER3_THRESHOLD:
                company_row = paw_all.iloc[best_match['company_idx']]
                is_verified = (company_row['has_ticker'] == 1) or (company_row['has_gvkey'] == 1)
                tier3_records.append({
                    'SAFEGRAPH_BRAND_ID': brand_row['SAFEGRAPH_BRAND_ID'],
                    'BRAND_NAME': brand_row['BRAND_NAME'],
                    'STOCK_SYMBOL': brand_row['STOCK_SYMBOL'],
                    'NAICS_CODE': brand_row['NAICS_CODE'],
                    'rcid': company_row['rcid'],
                    'company_name': company_row['company_name'],
                    'gvkey': company_row['gvkey'] if pd.notna(company_row['gvkey']) else None,
                    'is_verified': is_verified,
                    'final_parent_company': company_row['final_parent_company'] if 'final_parent_company' in company_row.index else None,
                    'final_parent_company_rcid': company_row['final_parent_company_rcid'] if 'final_parent_company_rcid' in company_row.index else None,
                    'match_tier': 3,
                    'match_method': 'semantic_fuzzy',
                    'confidence': best_match['combined_score'],
                    'cos_sim': best_match['cos_sim'],
                    'jaro_winkler': best_match['jaro_winkler'],
                    'jaro_winkler_norm': best_match['jaro_winkler_norm'],
                    'token_jaccard': best_match['token_jaccard'],
                    'contains_match': best_match['contains_match']
                })

    tier3 = pd.DataFrame(tier3_records)
    print(f"  Tier 3 matches: {len(tier3)} brands")

    return tier3


def main():
    print("=" * 70)
    print("TIERED ENTITY RESOLUTION: SafeGraph Brands → PAW Companies")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1] Loading data...")
    sg = pd.read_parquet(SAFEGRAPH_BRANDS)
    paw = pd.read_parquet(PAW_COMPANIES)

    print(f"  SafeGraph brands: {len(sg)}")
    print(f"  PAW companies: {len(paw)}")

    tier1 = tier1_ticker_matching(sg, paw)

    tier2 = tier2_parent_inheritance(sg, tier1)

    matched_brand_ids = set(tier1['SAFEGRAPH_BRAND_ID'].unique()) | set(tier2['SAFEGRAPH_BRAND_ID'].unique() if len(tier2) > 0 else [])

    client = OpenAI()
    tier3 = tier3_fuzzy_matching(sg, paw, matched_brand_ids, client)

    print("\n" + "=" * 70)
    print("COMBINING RESULTS")
    print("=" * 70)

    all_matches = pd.concat([tier1, tier2, tier3], ignore_index=True)

    print(f"\n  Total matches: {len(all_matches)}")
    print(f"    Tier 1 (ticker): {len(tier1)}")
    print(f"    Tier 2 (parent): {len(tier2)}")
    print(f"    Tier 3 (fuzzy):  {len(tier3)}")
    print(f"  Unmatched brands: {len(sg) - len(all_matches)}")

    output_file = OUTPUT_DIR / "brand_matches_tiered.parquet"
    all_matches.to_parquet(output_file, index=False)
    print(f"\n  Saved to: {output_file}")

    print("\n" + "=" * 70)
    print("QUALITY SUMMARY")
    print("=" * 70)

    tier1_verified = len(tier1[tier1['gvkey'].notna()])
    tier3_high_conf = len(tier3[tier3['confidence'] >= 0.85]) if len(tier3) > 0 else 0
    tier3_med_conf = len(tier3[(tier3['confidence'] >= 0.75) & (tier3['confidence'] < 0.85)]) if len(tier3) > 0 else 0

    print(f"  Tier 1 with gvkey: {tier1_verified}")
    print(f"  Tier 3 high confidence (>=0.85): {tier3_high_conf}")
    print(f"  Tier 3 medium confidence (0.75-0.85): {tier3_med_conf}")

    print("\n  Sample Tier 1 matches:")
    print(tier1[['BRAND_NAME', 'company_name', 'STOCK_SYMBOL']].head(10).to_string())

    if len(tier3) > 0:
        print("\n  Sample Tier 3 matches (high confidence):")
        tier3_sample = tier3.sort_values('confidence', ascending=False).head(10)
        print(tier3_sample[['BRAND_NAME', 'company_name', 'confidence']].to_string())

    print("\nDone!")


if __name__ == "__main__":
    main()
