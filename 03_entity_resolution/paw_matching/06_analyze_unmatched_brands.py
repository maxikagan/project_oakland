#!/usr/bin/env python3
"""
Analyze unmatched brands and their best similarity scores to find potential additional matches.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

INPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')
CACHE_DIR = INPUT_DIR / 'embedding_cache'

print("Loading data...")

# Load brands and matched brands
brands = pd.read_parquet(INPUT_DIR / 'advan_brands.parquet')
matches = pd.read_parquet(INPUT_DIR / 'brand_matches_validated.parquet')
companies = pd.read_parquet(INPUT_DIR / 'paw_companies_for_matching.parquet')

matched_brand_ids = set(matches['safegraph_brand_id'])
unmatched = brands[~brands['safegraph_brand_id'].isin(matched_brand_ids)].copy()
unmatched = unmatched.sort_values('n_locations', ascending=False)

print(f"\nTotal brands: {len(brands):,}")
print(f"Matched brands: {len(matches):,}")
print(f"Unmatched brands: {len(unmatched):,}")
print(f"\nUnmatched locations: {unmatched['n_locations'].sum():,}")

# Load embeddings
print("\nLoading embeddings...")
with open(CACHE_DIR / 'brand_embeddings.json', 'r') as f:
    brand_emb_list = json.load(f)
with open(CACHE_DIR / 'company_embeddings.json', 'r') as f:
    company_emb_list = json.load(f)

brand_matrix = np.array(brand_emb_list)
company_matrix = np.array(company_emb_list)

# Normalize for cosine similarity
brand_norms = np.linalg.norm(brand_matrix, axis=1, keepdims=True)
company_norms = np.linalg.norm(company_matrix, axis=1, keepdims=True)
brand_matrix_norm = brand_matrix / (brand_norms + 1e-10)
company_matrix_norm = company_matrix / (company_norms + 1e-10)

print(f"Brand embeddings: {brand_matrix.shape}")
print(f"Company embeddings: {company_matrix.shape}")

# Get best similarity for each unmatched brand
print("\nComputing best similarities for unmatched brands...")

# Create brand name to index mapping
brand_name_to_idx = {name: idx for idx, name in enumerate(brands['brand_name'].tolist())}

results = []
for _, row in unmatched.iterrows():
    brand_name = row['brand_name']
    brand_idx = brand_name_to_idx.get(brand_name)

    if brand_idx is None:
        continue

    similarities = np.dot(company_matrix_norm, brand_matrix_norm[brand_idx])
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]

    best_company = companies.iloc[best_idx]

    results.append({
        'brand_name': brand_name,
        'n_locations': row['n_locations'],
        'best_similarity': best_score,
        'best_company': best_company['company_name'],
        'best_rcid': best_company['rcid'],
        'has_gvkey': best_company['has_gvkey'],
        'has_ticker': best_company['has_ticker'],
    })

results_df = pd.DataFrame(results)

# Analyze by similarity threshold
print("\n" + "=" * 70)
print("UNMATCHED BRANDS BY BEST SIMILARITY SCORE")
print("=" * 70)

thresholds = [0.77, 0.76, 0.75, 0.70, 0.65, 0.60]
for thresh in thresholds:
    above = results_df[results_df['best_similarity'] >= thresh]
    print(f"\n>= {thresh}: {len(above):,} brands, {above['n_locations'].sum():,} locations")

# Show brands close to threshold (0.75-0.78)
print("\n" + "=" * 70)
print("BRANDS CLOSE TO THRESHOLD (0.75-0.78) - TOP 30 BY LOCATIONS")
print("=" * 70)

close = results_df[(results_df['best_similarity'] >= 0.75) & (results_df['best_similarity'] < 0.78)]
close = close.sort_values('n_locations', ascending=False).head(30)

for _, row in close.iterrows():
    gvkey_str = " [has GVKey]" if row['has_gvkey'] else ""
    print(f"\n{row['brand_name']} ({row['n_locations']:,} locs) -> {row['best_company']}{gvkey_str}")
    print(f"  Similarity: {row['best_similarity']:.3f}")

# Show largest unmatched brands regardless of score
print("\n" + "=" * 70)
print("TOP 30 UNMATCHED BRANDS BY LOCATION COUNT")
print("=" * 70)

top_unmatched = results_df.sort_values('n_locations', ascending=False).head(30)
for _, row in top_unmatched.iterrows():
    gvkey_str = " [has GVKey]" if row['has_gvkey'] else ""
    print(f"\n{row['brand_name']} ({row['n_locations']:,} locs)")
    print(f"  Best match: {row['best_company']}{gvkey_str} @ {row['best_similarity']:.3f}")

# Categories of unmatched
print("\n" + "=" * 70)
print("SUMMARY: CATEGORIES OF UNMATCHED BRANDS")
print("=" * 70)

# ATM networks
atm_keywords = ['ATM', 'Bitcoin ATM', 'Charger', 'Charging', 'Drop Box', 'Collection Point', 'Kiosk']
atm_brands = results_df[results_df['brand_name'].str.contains('|'.join(atm_keywords), case=False, na=False)]
print(f"\nATM/Kiosk/Charger networks: {len(atm_brands):,} brands, {atm_brands['n_locations'].sum():,} locations")

# Potential manual matches (high location count, decent similarity)
potential = results_df[(results_df['n_locations'] >= 500) & (results_df['best_similarity'] >= 0.70)]
print(f"Potential manual matches (>=500 locs, >=0.70 sim): {len(potential):,} brands, {potential['n_locations'].sum():,} locations")

# Very low similarity (likely no good match exists)
low_sim = results_df[results_df['best_similarity'] < 0.60]
print(f"Very low similarity (<0.60): {len(low_sim):,} brands, {low_sim['n_locations'].sum():,} locations")
