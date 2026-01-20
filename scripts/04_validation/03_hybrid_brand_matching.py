#!/usr/bin/env python3
"""
Task 2.2: Hybrid brand matching using fuzzylink-style approach.

Combines:
1. Cosine similarity from text embeddings (text-embedding-3-large)
2. Jaro-Winkler string distance
3. Manual labeling of candidate matches
4. Logistic regression calibration

Based on Ornstein (2025) "Probabilistic Record Linkage Using Pretrained Text Embeddings"

Requires: OPENAI_API_KEY environment variable
"""

import os
import json
import time
import re
from pathlib import Path
import numpy as np
import pandas as pd
from jellyfish import jaro_winkler_similarity

if 'OPENAI_API_KEY' not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable not set")

from openai import OpenAI

SCRATCH = Path('/global/scratch/users/maxkagan/measuring_stakeholder_ideology')
HOME = Path('/global/home/users/maxkagan/measuring_stakeholder_ideology')

ADVAN_BRANDS_PATH = SCRATCH / 'outputs' / 'entity_resolution' / 'advan_brands.parquet'
BRAND_EMBEDDINGS_CACHE = SCRATCH / 'outputs' / 'entity_resolution' / 'embedding_cache' / 'brand_embeddings.json'
SCHOENMUELLER_PATH = HOME / 'reference' / 'other_measures' / 'schoenmueller_et_al' / 'social-listening_PoliticalAffiliation_2022_Dec.csv'
OUTPUT_DIR = SCRATCH / 'outputs' / 'validation'

TOP_K_CANDIDATES = 10
EMBEDDING_MODEL = "text-embedding-3-large"
BATCH_SIZE = 100


def normalize_brand_name(name: str) -> str:
    """Normalize brand name for Jaro-Winkler comparison."""
    if pd.isna(name):
        return ''
    name = str(name).lower()
    name = re.sub(r"['\-\.\,\&\(\)\_]", '', name)
    name = re.sub(r'\s+', '', name)
    return name.strip()


def load_data():
    """Load Advan brands, embeddings, and Schoenmueller data."""
    print("=== Loading data ===")

    advan = pd.read_parquet(ADVAN_BRANDS_PATH)
    advan = advan.sort_values('n_locations', ascending=False).reset_index(drop=True)
    print(f"Advan brands: {len(advan):,}")

    with open(BRAND_EMBEDDINGS_CACHE, 'r') as f:
        advan_embeddings = np.array(json.load(f))
    print(f"Advan embeddings: {advan_embeddings.shape}")

    if len(advan) != len(advan_embeddings):
        min_len = min(len(advan), len(advan_embeddings))
        advan = advan.head(min_len)
        advan_embeddings = advan_embeddings[:min_len]

    schoen = pd.read_csv(SCHOENMUELLER_PATH)
    schoen = schoen.rename(columns={
        'Brand_Name': 'schoen_brand',
        'Proportion Republicans': 'schoen_rep_prop',
        'Proportion Democrats': 'schoen_dem_prop'
    })
    print(f"Schoenmueller brands: {len(schoen):,}")

    return advan, advan_embeddings, schoen


def generate_schoenmueller_embeddings_large(client, schoen_brands):
    """Generate embeddings using text-embedding-3-large."""
    print(f"\n=== Generating Schoenmueller embeddings ({EMBEDDING_MODEL}) ===")

    cache_file = OUTPUT_DIR / f'schoenmueller_embeddings_large.json'
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if cache_file.exists():
        print(f"Loading cached embeddings from {cache_file}")
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        if len(cached) == len(schoen_brands):
            return np.array(cached)
        print(f"Cache size mismatch, regenerating...")

    all_embeddings = []
    total_batches = (len(schoen_brands) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(schoen_brands), BATCH_SIZE):
        batch = schoen_brands[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches}...")

        for attempt in range(3):
            try:
                response = client.embeddings.create(
                    input=batch,
                    model=EMBEDDING_MODEL
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
                time.sleep(0.1)
                break
            except Exception as e:
                wait_time = 5 * (2 ** attempt)
                print(f"    Error: {e}, retrying in {wait_time}s (attempt {attempt + 1}/3)...")
                time.sleep(wait_time)
                if attempt == 2:
                    raise RuntimeError(f"Failed after 3 attempts on batch {batch_num}")

    with open(cache_file, 'w') as f:
        json.dump(all_embeddings, f)
    print(f"Cached to {cache_file}")

    return np.array(all_embeddings)


def regenerate_advan_embeddings_large(client, advan_brands):
    """Regenerate Advan embeddings using text-embedding-3-large."""
    print(f"\n=== Generating Advan embeddings ({EMBEDDING_MODEL}) ===")

    cache_file = OUTPUT_DIR / 'advan_embeddings_large.json'

    if cache_file.exists():
        print(f"Loading cached embeddings from {cache_file}")
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        if len(cached) == len(advan_brands):
            return np.array(cached)
        print(f"Cache size mismatch, regenerating...")

    all_embeddings = []
    total_batches = (len(advan_brands) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(advan_brands), BATCH_SIZE):
        batch = advan_brands[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        if batch_num % 10 == 0 or batch_num == total_batches:
            print(f"  Batch {batch_num}/{total_batches}...")

        for attempt in range(3):
            try:
                response = client.embeddings.create(
                    input=batch,
                    model=EMBEDDING_MODEL
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
                time.sleep(0.1)
                break
            except Exception as e:
                wait_time = 5 * (2 ** attempt)
                print(f"    Error: {e}, retrying in {wait_time}s (attempt {attempt + 1}/3)...")
                time.sleep(wait_time)
                if attempt == 2:
                    raise RuntimeError(f"Failed after 3 attempts on batch {batch_num}")

    with open(cache_file, 'w') as f:
        json.dump(all_embeddings, f)
    print(f"Cached to {cache_file}")

    return np.array(all_embeddings)


def compute_candidate_matches(schoen_emb, advan_emb, schoen_df, advan_df, top_k=TOP_K_CANDIDATES):
    """Compute top-k candidate matches for each Schoenmueller brand."""
    print(f"\n=== Computing top-{top_k} candidates per brand ===")

    schoen_norm = schoen_emb / (np.linalg.norm(schoen_emb, axis=1, keepdims=True) + 1e-10)
    advan_norm = advan_emb / (np.linalg.norm(advan_emb, axis=1, keepdims=True) + 1e-10)

    similarities = np.dot(schoen_norm, advan_norm.T)

    candidates = []

    for i in range(len(schoen_df)):
        schoen_name = schoen_df.iloc[i]['schoen_brand']
        schoen_norm_name = normalize_brand_name(schoen_name)

        top_indices = np.argsort(similarities[i])[-top_k:][::-1]

        for rank, idx in enumerate(top_indices):
            advan_name = advan_df.iloc[idx]['brand_name']
            advan_norm_name = normalize_brand_name(advan_name)

            cosine_sim = float(similarities[i, idx])
            if not schoen_norm_name or not advan_norm_name:
                jw_sim = 0.0
            else:
                jw_sim = jaro_winkler_similarity(schoen_norm_name, advan_norm_name)

            candidates.append({
                'schoen_brand': schoen_name,
                'schoen_rep_prop': schoen_df.iloc[i]['schoen_rep_prop'],
                'advan_brand': advan_name,
                'advan_brand_id': advan_df.iloc[idx]['safegraph_brand_id'],
                'advan_n_locations': int(advan_df.iloc[idx]['n_locations']),
                'cosine_sim': cosine_sim,
                'jaro_winkler': jw_sim,
                'rank': rank + 1
            })

    candidates_df = pd.DataFrame(candidates)
    print(f"Generated {len(candidates_df):,} candidate pairs")

    return candidates_df


def identify_likely_matches(candidates_df):
    """Pre-filter to identify likely matches for manual review."""

    high_jw = candidates_df[candidates_df['jaro_winkler'] >= 0.85].copy()
    high_jw['match_reason'] = 'high_jaro_winkler'

    high_cos_rank1 = candidates_df[(candidates_df['cosine_sim'] >= 0.85) & (candidates_df['rank'] == 1)].copy()
    high_cos_rank1['match_reason'] = 'high_cosine_rank1'

    combined = pd.concat([high_jw, high_cos_rank1]).drop_duplicates(
        subset=['schoen_brand', 'advan_brand']
    )

    combined['combined_score'] = 0.5 * combined['cosine_sim'] + 0.5 * combined['jaro_winkler']
    combined = combined.sort_values('combined_score', ascending=False)

    print(f"\n=== Likely matches for review ===")
    print(f"High Jaro-Winkler (>=0.85): {len(high_jw)}")
    print(f"High Cosine + Rank 1 (>=0.85): {len(high_cos_rank1)}")
    print(f"Combined unique: {len(combined)}")

    return combined


def main():
    print("=" * 60)
    print("Task 2.2: Hybrid Brand Matching (fuzzylink approach)")
    print("=" * 60)

    client = OpenAI()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    advan, _, schoen = load_data()  # Ignore cached small embeddings, regenerate with large model

    schoen_emb = generate_schoenmueller_embeddings_large(
        client,
        schoen['schoen_brand'].tolist()
    )

    advan_emb = regenerate_advan_embeddings_large(
        client,
        advan['brand_name'].tolist()
    )

    candidates = compute_candidate_matches(schoen_emb, advan_emb, schoen, advan)
    candidates.to_parquet(OUTPUT_DIR / 'brand_match_candidates.parquet', index=False)

    likely_matches = identify_likely_matches(candidates)
    likely_matches.to_csv(OUTPUT_DIR / 'likely_matches_for_review.csv', index=False)

    print(f"\n=== Sample likely matches ===")
    for _, row in likely_matches.head(30).iterrows():
        print(f"  {row['schoen_brand']:25} -> {row['advan_brand']:30} "
              f"(cos={row['cosine_sim']:.3f}, jw={row['jaro_winkler']:.3f})")

    print(f"\nAll candidates: {OUTPUT_DIR / 'brand_match_candidates.parquet'}")
    print(f"Likely matches: {OUTPUT_DIR / 'likely_matches_for_review.csv'}")

    print("\n" + "=" * 60)
    print("Next step: Manual review of likely_matches_for_review.csv")
    print("=" * 60)


if __name__ == '__main__':
    main()
