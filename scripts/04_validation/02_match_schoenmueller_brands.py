#!/usr/bin/env python3
"""
Task 2.2: Match Schoenmueller brands to Advan brands using semantic similarity.

Uses OpenAI text-embedding-3-small embeddings (same as entity resolution).
Leverages cached Advan brand embeddings from entity resolution work.

Requires: OPENAI_API_KEY environment variable
"""

import os
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

if 'OPENAI_API_KEY' not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable not set")

from openai import OpenAI

SCRATCH = Path('/global/scratch/users/maxkagan/measuring_stakeholder_ideology')
HOME = Path('/global/home/users/maxkagan/measuring_stakeholder_ideology')

ADVAN_BRANDS_PATH = SCRATCH / 'outputs' / 'entity_resolution' / 'advan_brands.parquet'
BRAND_EMBEDDINGS_CACHE = SCRATCH / 'outputs' / 'entity_resolution' / 'embedding_cache' / 'brand_embeddings.json'
SCHOENMUELLER_PATH = HOME / 'reference' / 'other_measures' / 'schoenmueller_et_al' / 'social-listening_PoliticalAffiliation_2022_Dec.csv'
OUTPUT_DIR = SCRATCH / 'outputs' / 'validation'

SIMILARITY_THRESHOLD_HIGH = 0.85
SIMILARITY_THRESHOLD_LOW = 0.75
BATCH_SIZE = 100


def load_advan_brands_and_embeddings():
    """Load Advan brands and their cached embeddings.

    IMPORTANT: Embeddings in brand_embeddings.json are ordered by n_locations DESC,
    matching the sort order used in 03_match_brands_embeddings.py during generation.
    """
    print("=== Loading Advan brands and embeddings ===")

    brands = pd.read_parquet(ADVAN_BRANDS_PATH)
    brands = brands.sort_values('n_locations', ascending=False).reset_index(drop=True)
    print(f"Loaded {len(brands):,} Advan brands")

    with open(BRAND_EMBEDDINGS_CACHE, 'r') as f:
        embeddings = json.load(f)
    embeddings = np.array(embeddings)
    print(f"Loaded embeddings: {embeddings.shape}")

    if len(brands) != len(embeddings):
        print(f"WARNING: Brand count ({len(brands)}) != embedding count ({len(embeddings)})")
        min_len = min(len(brands), len(embeddings))
        brands = brands.head(min_len)
        embeddings = embeddings[:min_len]

    return brands, embeddings


def load_schoenmueller():
    """Load Schoenmueller validation data."""
    print("\n=== Loading Schoenmueller data ===")

    schoen = pd.read_csv(SCHOENMUELLER_PATH)
    schoen = schoen.rename(columns={
        'Brand_Name': 'schoen_brand',
        'Proportion Republicans': 'schoen_rep_prop',
        'Proportion Democrats': 'schoen_dem_prop'
    })
    print(f"Loaded {len(schoen):,} Schoenmueller brands")

    return schoen


def generate_schoenmueller_embeddings(client, schoen_brands):
    """Generate embeddings for Schoenmueller brand names."""
    print("\n=== Generating Schoenmueller embeddings ===")

    cache_file = OUTPUT_DIR / 'schoenmueller_embeddings.json'
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
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} brands)...")

        try:
            response = client.embeddings.create(
                input=batch,
                model="text-embedding-3-small"
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
            time.sleep(0.1)
        except Exception as e:
            print(f"    Error on batch {batch_num}: {e}")
            print(f"    Retrying in 5 seconds...")
            time.sleep(5)
            response = client.embeddings.create(
                input=batch,
                model="text-embedding-3-small"
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

    with open(cache_file, 'w') as f:
        json.dump(all_embeddings, f)
    print(f"Cached to {cache_file}")

    return np.array(all_embeddings)


def compute_matches(schoen_embeddings, advan_embeddings, schoen_df, advan_df):
    """Find best Advan match for each Schoenmueller brand."""
    print("\n=== Computing semantic similarity matches ===")

    schoen_norms = np.linalg.norm(schoen_embeddings, axis=1, keepdims=True)
    advan_norms = np.linalg.norm(advan_embeddings, axis=1, keepdims=True)

    schoen_norm = schoen_embeddings / (schoen_norms + 1e-10)
    advan_norm = advan_embeddings / (advan_norms + 1e-10)

    similarities = np.dot(schoen_norm, advan_norm.T)

    matches = []

    for i in range(len(schoen_df)):
        best_idx = np.argmax(similarities[i])
        best_score = similarities[i, best_idx]

        second_best_idx = np.argsort(similarities[i])[-2]
        second_best_score = similarities[i, second_best_idx]

        if best_score >= SIMILARITY_THRESHOLD_LOW:
            confidence = 'high' if best_score >= SIMILARITY_THRESHOLD_HIGH else 'medium'
        else:
            confidence = 'low'

        matches.append({
            'schoen_brand': schoen_df.iloc[i]['schoen_brand'],
            'schoen_rep_prop': schoen_df.iloc[i]['schoen_rep_prop'],
            'schoen_dem_prop': schoen_df.iloc[i]['schoen_dem_prop'],
            'advan_brand': advan_df.iloc[best_idx]['brand_name'],
            'advan_brand_id': advan_df.iloc[best_idx]['safegraph_brand_id'],
            'advan_n_locations': int(advan_df.iloc[best_idx]['n_locations']),
            'similarity': float(best_score),
            'second_best_advan': advan_df.iloc[second_best_idx]['brand_name'],
            'second_best_similarity': float(second_best_score),
            'confidence': confidence
        })

    matches_df = pd.DataFrame(matches)

    print(f"\nMatch summary:")
    print(f"  Total Schoenmueller brands: {len(matches_df)}")
    print(f"  High confidence (>={SIMILARITY_THRESHOLD_HIGH}): {len(matches_df[matches_df['confidence'] == 'high'])}")
    print(f"  Medium confidence ({SIMILARITY_THRESHOLD_LOW}-{SIMILARITY_THRESHOLD_HIGH}): {len(matches_df[matches_df['confidence'] == 'medium'])}")
    print(f"  Low confidence (<{SIMILARITY_THRESHOLD_LOW}): {len(matches_df[matches_df['confidence'] == 'low'])}")

    return matches_df


def print_sample_matches(matches_df, n=30):
    """Print sample matches for manual review."""
    print("\n=== Sample High-Confidence Matches ===")
    high_conf = matches_df[matches_df['confidence'] == 'high'].head(n)
    for _, row in high_conf.iterrows():
        print(f"  {row['schoen_brand']:25} -> {row['advan_brand']:30} (sim={row['similarity']:.3f})")

    print("\n=== Sample Medium-Confidence Matches (Review Needed) ===")
    med_conf = matches_df[matches_df['confidence'] == 'medium'].head(n)
    for _, row in med_conf.iterrows():
        print(f"  {row['schoen_brand']:25} -> {row['advan_brand']:30} (sim={row['similarity']:.3f})")
        print(f"    2nd best: {row['second_best_advan']} (sim={row['second_best_similarity']:.3f})")

    print("\n=== Sample Low-Confidence Matches (Likely No Match) ===")
    low_conf = matches_df[matches_df['confidence'] == 'low'].head(n)
    for _, row in low_conf.iterrows():
        print(f"  {row['schoen_brand']:25} -> {row['advan_brand']:30} (sim={row['similarity']:.3f})")


def main():
    print("=" * 60)
    print("Task 2.2: Match Schoenmueller to Advan Brands")
    print("=" * 60)

    client = OpenAI()

    advan_brands, advan_embeddings = load_advan_brands_and_embeddings()
    schoen = load_schoenmueller()

    schoen_embeddings = generate_schoenmueller_embeddings(
        client,
        schoen['schoen_brand'].tolist()
    )

    matches = compute_matches(schoen_embeddings, advan_embeddings, schoen, advan_brands)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matches.to_parquet(OUTPUT_DIR / 'schoenmueller_brand_matches.parquet', index=False)
    matches.to_csv(OUTPUT_DIR / 'schoenmueller_brand_matches.csv', index=False)
    print(f"\nSaved matches to {OUTPUT_DIR}")

    print_sample_matches(matches)

    high_medium = matches[matches['confidence'].isin(['high', 'medium'])]
    print(f"\n=== Summary ===")
    print(f"Usable matches (high + medium confidence): {len(high_medium)}")
    print(f"Coverage: {len(high_medium) / len(schoen) * 100:.1f}% of Schoenmueller brands")

    print("\n" + "=" * 60)
    print("Task 2.2 complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
