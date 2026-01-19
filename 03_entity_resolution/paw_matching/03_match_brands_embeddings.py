#!/usr/bin/env python3
"""
Step 3: Match Advan brands to PAW companies using OpenAI embeddings.

This script:
1. Loads extracted brands and companies
2. Generates embeddings using OpenAI text-embedding-3-small
3. Computes cosine similarity
4. Outputs matches above threshold

Requires: OPENAI_API_KEY environment variable
"""

import os
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

# Check for API key early
if 'OPENAI_API_KEY' not in os.environ:
    raise ValueError("OPENAI_API_KEY environment variable not set")

import duckdb
from openai import OpenAI

INPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')
OUTPUT_DIR = INPUT_DIR
EMBEDDING_CACHE_DIR = INPUT_DIR / 'embedding_cache'

SIMILARITY_THRESHOLD = 0.78
BATCH_SIZE = 2000  # OpenAI recommends batches for efficiency


def load_data():
    """Load brands and companies from parquet files."""
    print("\n" + "=" * 60)
    print("Loading data...")
    print("=" * 60)

    con = duckdb.connect()

    brands = con.execute(f"""
        SELECT safegraph_brand_id, brand_name, n_locations, naics_code
        FROM parquet_scan('{INPUT_DIR}/advan_brands.parquet')
        ORDER BY n_locations DESC
    """).fetchdf()

    companies = con.execute(f"""
        SELECT rcid, company_name, gvkey, ticker, naics_code, has_ticker, has_gvkey
        FROM parquet_scan('{INPUT_DIR}/paw_companies_for_matching.parquet')
    """).fetchdf()

    con.close()

    print(f"  Loaded {len(brands):,} brands")
    print(f"  Loaded {len(companies):,} companies")

    return brands, companies


def get_embeddings_batch(client, texts, model="text-embedding-3-small"):
    """Get embeddings for a batch of texts."""
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [item.embedding for item in response.data]


def generate_embeddings(client, names, cache_file, entity_type):
    """Generate embeddings for a list of names, with caching."""
    print(f"\n  Generating embeddings for {len(names):,} {entity_type}...")

    EMBEDDING_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if cache_file.exists():
        print(f"    Loading cached embeddings from {cache_file}")
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

        if batch_num % 10 == 0 or batch_num == total_batches:
            print(f"    Processing batch {batch_num}/{total_batches}...")

        try:
            embeddings = get_embeddings_batch(client, batch)
            all_embeddings.extend(embeddings)

            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            print(f"    Error on batch {batch_num}: {e}")
            print(f"    Retrying in 5 seconds...")
            time.sleep(5)
            embeddings = get_embeddings_batch(client, batch)
            all_embeddings.extend(embeddings)

    # Cache embeddings
    with open(cache_file, 'w') as f:
        json.dump(all_embeddings, f)
    print(f"    Cached embeddings to {cache_file}")

    return np.array(all_embeddings)


def compute_matches(brand_embeddings, company_embeddings, brands, companies):
    """Compute cosine similarity and find best matches."""
    print("\n" + "=" * 60)
    print("Computing matches...")
    print("=" * 60)

    # Normalize embeddings for cosine similarity (add epsilon to prevent division by zero)
    brand_norms = np.linalg.norm(brand_embeddings, axis=1, keepdims=True)
    company_norms = np.linalg.norm(company_embeddings, axis=1, keepdims=True)

    brand_embeddings_norm = brand_embeddings / (brand_norms + 1e-10)
    company_embeddings_norm = company_embeddings / (company_norms + 1e-10)

    matches = []
    n_brands = len(brands)

    print(f"  Processing {n_brands:,} brands against {len(companies):,} companies...")

    for i in range(n_brands):
        if (i + 1) % 1000 == 0:
            print(f"    Processed {i + 1:,}/{n_brands:,} brands...")

        similarities = np.dot(company_embeddings_norm, brand_embeddings_norm[i])
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        if best_score >= SIMILARITY_THRESHOLD:
            brand_naics = brands.iloc[i]['naics_code']
            company_naics = companies.iloc[best_idx]['naics_code']

            gvkey = companies.iloc[best_idx]['gvkey']
            ticker = companies.iloc[best_idx]['ticker']

            matches.append({
                'safegraph_brand_id': brands.iloc[i]['safegraph_brand_id'],
                'brand_name': brands.iloc[i]['brand_name'],
                'brand_n_locations': int(brands.iloc[i]['n_locations']),
                'brand_naics': str(int(brand_naics)) if pd.notna(brand_naics) else None,
                'rcid': companies.iloc[best_idx]['rcid'],
                'company_name': companies.iloc[best_idx]['company_name'],
                'gvkey': gvkey if pd.notna(gvkey) and gvkey != 'NA' else None,
                'ticker': ticker if pd.notna(ticker) and ticker != 'NA' else None,
                'company_naics': str(company_naics) if pd.notna(company_naics) else None,
                'has_ticker': int(companies.iloc[best_idx]['has_ticker']),
                'has_gvkey': int(companies.iloc[best_idx]['has_gvkey']),
                'cosine_similarity': float(best_score),
            })

    print(f"\n  Found {len(matches):,} matches above threshold {SIMILARITY_THRESHOLD}")

    return matches


def save_matches(matches):
    """Save matches to parquet."""
    print("\n" + "=" * 60)
    print("Saving matches...")
    print("=" * 60)

    output_file = OUTPUT_DIR / 'brand_matches.parquet'

    # Create table from matches
    if matches:
        df = pd.DataFrame(matches)
        df.to_parquet(output_file, compression='snappy')

        con = duckdb.connect()

        # Summary stats
        stats = con.execute(f"""
            SELECT
                COUNT(*) as n_matches,
                SUM(has_ticker) as matches_with_ticker,
                SUM(has_gvkey) as matches_with_gvkey,
                AVG(cosine_similarity) as avg_similarity,
                MIN(cosine_similarity) as min_similarity,
                MAX(cosine_similarity) as max_similarity
            FROM parquet_scan('{output_file}')
        """).fetchone()

        print(f"  Total matches: {stats[0]:,}")
        print(f"  Matches with ticker: {stats[1]:,}")
        print(f"  Matches with GVKey: {stats[2]:,}")
        print(f"  Similarity - avg: {stats[3]:.3f}, min: {stats[4]:.3f}, max: {stats[5]:.3f}")
    else:
        print("  No matches found!")

    con.close()
    print(f"  Output: {output_file}")


def print_sample_matches(matches, n=20):
    """Print sample matches for review."""
    print("\n" + "=" * 60)
    print(f"Sample matches (top {n} by location count):")
    print("=" * 60)

    sorted_matches = sorted(matches, key=lambda x: -x['brand_n_locations'])[:n]

    for m in sorted_matches:
        id_str = ""
        if m['ticker']:
            id_str = f" [{m['ticker']}]"
        elif m['gvkey']:
            id_str = f" [GVKey:{m['gvkey']}]"
        print(f"  {m['brand_name']} ({m['brand_n_locations']:,} locs) -> {m['company_name']}{id_str}")
        print(f"    Similarity: {m['cosine_similarity']:.3f}")


def main():
    print("=" * 60)
    print("Step 3: Match Brands to Companies using Embeddings")
    print("=" * 60)
    print(f"Similarity threshold: {SIMILARITY_THRESHOLD}")

    # Initialize OpenAI client
    client = OpenAI()

    # Load data
    brands, companies = load_data()

    # Generate embeddings
    brand_names = brands['brand_name'].tolist()
    company_names = companies['company_name'].tolist()

    brand_cache = EMBEDDING_CACHE_DIR / 'brand_embeddings.json'
    company_cache = EMBEDDING_CACHE_DIR / 'company_embeddings.json'

    brand_embeddings = generate_embeddings(client, brand_names, brand_cache, "brands")
    company_embeddings = generate_embeddings(client, company_names, company_cache, "companies")

    # Compute matches
    matches = compute_matches(brand_embeddings, company_embeddings, brands, companies)

    # Save results
    save_matches(matches)

    # Print sample for review
    print_sample_matches(matches)

    print("\n" + "=" * 60)
    print("Step 3 complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
