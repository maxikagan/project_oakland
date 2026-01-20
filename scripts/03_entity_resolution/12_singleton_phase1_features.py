#!/usr/bin/env python3
"""
Phase 1: Compute features for singleton POI → PAW company matching.

FuzzyLink-style approach combining:
  - Cosine similarity from text embeddings
  - Jaro-Winkler string distance
  - Token Jaccard similarity
  - Contains match indicator

For each unique POI location_name, finds top-K candidate companies by
embedding similarity, then computes all features for the logit model.

Usage: python 12_singleton_phase1_features.py --msa columbus_oh
"""

import argparse
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
POI_DIR = PROJECT_DIR / "outputs" / "entity_resolution" / "unbranded_pois_by_msa"
PAW_FILE = PROJECT_DIR / "outputs" / "entity_resolution" / "paw_company_by_msa.parquet"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "singleton_matching"
CACHE_DIR = OUTPUT_DIR / "embedding_cache"

TOP_K = 50
EMBEDDING_MODEL = "text-embedding-3-large"
BATCH_SIZE = 2000


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
    """Check if one string is contained in the other (case-insensitive)."""
    a_lower = a.lower()
    b_lower = b.lower()
    return a_lower in b_lower or b_lower in a_lower


def get_embeddings_batch(client: OpenAI, texts: list, model: str = EMBEDDING_MODEL) -> list:
    """Get embeddings for a batch of texts."""
    response = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in response.data]


def generate_embeddings(client: OpenAI, names: list, cache_file: Path, desc: str) -> np.ndarray:
    """Generate embeddings with caching."""
    print(f"  Generating embeddings for {len(names):,} {desc}...")

    if cache_file.exists():
        print(f"    Loading from cache: {cache_file.name}")
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        if len(cached) == len(names):
            return np.array(cached)
        print(f"    Cache size mismatch ({len(cached)} vs {len(names)}), regenerating...")

    all_embeddings = []
    total_batches = (len(names) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(names), BATCH_SIZE):
        batch = names[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        if batch_num % 5 == 0 or batch_num == total_batches:
            print(f"    Batch {batch_num}/{total_batches}...")

        try:
            embeddings = get_embeddings_batch(client, batch)
            all_embeddings.extend(embeddings)
            time.sleep(0.1)
        except Exception as e:
            print(f"    Error on batch {batch_num}: {e}, retrying...")
            time.sleep(5)
            embeddings = get_embeddings_batch(client, batch)
            all_embeddings.extend(embeddings)

    with open(cache_file, 'w') as f:
        json.dump(all_embeddings, f)
    print(f"    Cached to {cache_file.name}")

    return np.array(all_embeddings)


def find_top_k_candidates(poi_embeddings: np.ndarray, company_embeddings: np.ndarray, k: int = TOP_K) -> tuple:
    """
    For each POI embedding, find top-K company candidates by cosine similarity.
    Returns (indices, similarities) arrays of shape (n_pois, k).
    """
    print(f"  Finding top-{k} candidates for {len(poi_embeddings):,} POI names...")

    poi_norms = np.linalg.norm(poi_embeddings, axis=1, keepdims=True)
    company_norms = np.linalg.norm(company_embeddings, axis=1, keepdims=True)

    poi_normalized = poi_embeddings / (poi_norms + 1e-10)
    company_normalized = company_embeddings / (company_norms + 1e-10)

    n_pois = len(poi_embeddings)
    top_indices = np.zeros((n_pois, k), dtype=np.int32)
    top_sims = np.zeros((n_pois, k), dtype=np.float32)

    chunk_size = 1000
    for start in range(0, n_pois, chunk_size):
        end = min(start + chunk_size, n_pois)
        if start % 5000 == 0:
            print(f"    Processing POIs {start:,}-{end:,}...")

        chunk = poi_normalized[start:end]
        similarities = np.dot(chunk, company_normalized.T)

        for i, sim_row in enumerate(similarities):
            idx = start + i
            top_k_idx = np.argpartition(sim_row, -k)[-k:]
            top_k_idx = top_k_idx[np.argsort(sim_row[top_k_idx])[::-1]]
            top_indices[idx] = top_k_idx
            top_sims[idx] = sim_row[top_k_idx]

    return top_indices, top_sims


def compute_features(poi_names: list, company_names: list, top_indices: np.ndarray, top_sims: np.ndarray) -> pd.DataFrame:
    """Compute all features for candidate pairs."""
    print(f"  Computing features for {len(poi_names) * TOP_K:,} candidate pairs...")

    records = []

    for poi_idx, poi_name in enumerate(poi_names):
        if poi_idx % 5000 == 0:
            print(f"    Processing POI {poi_idx:,}/{len(poi_names):,}...")

        for rank in range(TOP_K):
            company_idx = top_indices[poi_idx, rank]
            company_name = company_names[company_idx]
            cos_sim = top_sims[poi_idx, rank]

            records.append({
                'poi_name_idx': poi_idx,
                'company_idx': company_idx,
                'location_name': poi_name,
                'company_name': company_name,
                'cos_sim': float(cos_sim),
                'jaro_winkler': jellyfish.jaro_winkler_similarity(poi_name, company_name),
                'token_jaccard': token_jaccard(poi_name, company_name),
                'contains_match': contains_match(poi_name, company_name),
            })

    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--msa', required=True, help='MSA name (e.g., columbus_oh)')
    args = parser.parse_args()

    msa = args.msa
    print("=" * 70)
    print(f"Phase 1: Compute Features for Singleton Matching - {msa}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1] Loading data...")
    poi_file = POI_DIR / f"{msa}.parquet"
    if not poi_file.exists():
        raise FileNotFoundError(f"POI file not found: {poi_file}")

    pois = pd.read_parquet(poi_file)
    print(f"  Loaded {len(pois):,} unbranded POIs")

    paw = pd.read_parquet(PAW_FILE)
    paw_msa = paw[paw['msa'] == msa].copy()
    print(f"  Loaded {len(paw_msa):,} PAW companies in {msa}")

    unique_poi_names = pois['location_name'].unique().tolist()
    unique_company_names = paw_msa['company_name'].unique().tolist()
    print(f"  Unique POI names: {len(unique_poi_names):,}")
    print(f"  Unique company names: {len(unique_company_names):,}")

    poi_name_to_placekeys = pois.groupby('location_name')['placekey'].apply(list).to_dict()
    company_name_to_rcids = paw_msa.groupby('company_name')['rcid'].apply(lambda x: list(x.unique())).to_dict()

    print("\n[2] Generating embeddings...")
    client = OpenAI()

    poi_cache = CACHE_DIR / f"{msa}_poi_embeddings.json"
    company_cache = CACHE_DIR / f"{msa}_company_embeddings.json"

    poi_embeddings = generate_embeddings(client, unique_poi_names, poi_cache, "POI names")
    company_embeddings = generate_embeddings(client, unique_company_names, company_cache, "company names")

    print("\n[3] Finding top-K candidates...")
    top_indices, top_sims = find_top_k_candidates(poi_embeddings, company_embeddings, TOP_K)

    print("\n[4] Computing features...")
    candidates = compute_features(unique_poi_names, unique_company_names, top_indices, top_sims)

    candidates['placekeys'] = candidates['location_name'].map(poi_name_to_placekeys)
    candidates['rcids'] = candidates['company_name'].map(company_name_to_rcids)
    candidates['n_pois'] = candidates['placekeys'].apply(len)
    candidates['msa'] = msa

    print("\n[5] Saving output...")
    output_file = OUTPUT_DIR / f"{msa}_candidate_pairs.parquet"
    candidates.to_parquet(output_file, index=False)
    print(f"  Saved {len(candidates):,} candidate pairs to {output_file}")

    print("\n[6] Summary statistics...")
    print(f"  cos_sim:      mean={candidates['cos_sim'].mean():.3f}, "
          f"min={candidates['cos_sim'].min():.3f}, max={candidates['cos_sim'].max():.3f}")
    print(f"  jaro_winkler: mean={candidates['jaro_winkler'].mean():.3f}, "
          f"min={candidates['jaro_winkler'].min():.3f}, max={candidates['jaro_winkler'].max():.3f}")
    print(f"  token_jaccard: mean={candidates['token_jaccard'].mean():.3f}")
    print(f"  contains_match: {candidates['contains_match'].sum():,} pairs ({100*candidates['contains_match'].mean():.1f}%)")

    high_sim = candidates[candidates['cos_sim'] >= 0.9]
    print(f"\n  High-similarity pairs (cos_sim >= 0.9): {len(high_sim):,}")

    print("\n  Sample high-similarity pairs:")
    sample = high_sim.nlargest(10, 'cos_sim')[['location_name', 'company_name', 'cos_sim', 'jaro_winkler']]
    print(sample.to_string(index=False))

    print("\n" + "=" * 70)
    print("Phase 1 complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
