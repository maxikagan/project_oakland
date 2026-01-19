#!/usr/bin/env python3
"""Check similarity scores for major unmatched brands."""

import json
import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')

def main():
    print("Loading data...", flush=True)
    brands = pd.read_parquet(OUTPUT_DIR / 'advan_brands.parquet')
    companies = pd.read_parquet(OUTPUT_DIR / 'paw_companies_for_matching.parquet')
    matches = pd.read_parquet(OUTPUT_DIR / 'brand_matches.parquet')

    print("Loading embeddings...", flush=True)
    with open(OUTPUT_DIR / 'embedding_cache/brand_embeddings.json', 'r') as f:
        brand_emb_list = json.load(f)
    with open(OUTPUT_DIR / 'embedding_cache/company_embeddings.json', 'r') as f:
        company_emb_list = json.load(f)

    brand_matrix = np.array(brand_emb_list)
    company_matrix = np.array(company_emb_list)

    print(f"Brand embeddings shape: {brand_matrix.shape}", flush=True)
    print(f"Company embeddings shape: {company_matrix.shape}", flush=True)

    company_norms = np.linalg.norm(company_matrix, axis=1)
    company_norms[company_norms == 0] = 1e-10

    matched_ids = set(matches.safegraph_brand_id)
    unmatched_mask = ~brands.safegraph_brand_id.isin(matched_ids)
    unmatched = brands[unmatched_mask].copy()
    unmatched_indices = brands[unmatched_mask].index.tolist()
    unmatched = unmatched.sort_values('n_locations', ascending=False)

    print("\n" + "="*70, flush=True)
    print("TOP 50 UNMATCHED BRANDS - BEST SIMILARITY SCORES", flush=True)
    print("="*70, flush=True)

    for _, row in unmatched.head(50).iterrows():
        brand_name = row['brand_name']
        brand_idx = row.name

        brand_vec = brand_matrix[brand_idx]
        brand_norm = np.linalg.norm(brand_vec)
        if brand_norm == 0:
            print(f"\n{brand_name} ({row['n_locations']:,} locs): ZERO EMBEDDING", flush=True)
            continue

        sims = np.dot(company_matrix, brand_vec) / (company_norms * brand_norm)
        top_indices = np.argsort(sims)[-5:][::-1]

        print(f"\n{brand_name} ({row['n_locations']:,} locs):", flush=True)
        for idx in top_indices:
            company_row = companies.iloc[idx]
            company_name = company_row['company_name']
            sim = sims[idx]
            gvkey = company_row['gvkey']
            gvkey_str = f" [GVKey:{gvkey}]" if pd.notna(gvkey) else ""
            marker = " * WOULD MATCH" if sim >= 0.80 else ""
            print(f"  {sim:.3f}  {company_name}{gvkey_str}{marker}", flush=True)

if __name__ == "__main__":
    main()
