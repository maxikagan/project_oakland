#!/usr/bin/env python3
"""
Apply manual corrections to brand matches for false positives.
Fixes data type issues before saving.
"""

import pandas as pd
import numpy as np
from pathlib import Path

INPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')

# Load current validated matches
matches = pd.read_parquet(INPUT_DIR / 'brand_matches_validated.parquet')
companies = pd.read_parquet(INPUT_DIR / 'paw_companies_for_matching.parquet')

print(f"Loaded {len(matches):,} validated matches")
print(f"Loaded {len(companies):,} companies for lookup")

# Manual corrections: brand_name -> (correct_rcid, correct_company_name)
manual_corrections = {
    'Mobil': (912348, 'Exxon Mobil Corp.'),
    'Boost Mobile': (2424544, 'Boost Mobile Select Retailer'),
    'Krispy Krunchy Chicken': (884399, 'Krispy Krunchy Foods LLC'),
    'Amazon Distribution': (1359692, 'Amazon.com, Inc.'),
    'Ferguson': (771909, 'Ferguson Enterprises LLC'),
    'Comfort Inn': (1060353, 'Comfort Inn & Suites Inc'),
    'TD Bank': (924743, 'TD Bank US Holding Co.'),
    'Aspen Dental': (360870, 'Aspen Dental Management, Inc.'),
    'Burlington': (260161, 'Burlington Stores, Inc.'),
    'Mathnasium': (754228, 'Mathnasium LLC'),
    'The Joint': (1218970, 'The Joint Corp.'),
    "Dick's Sporting Goods": (606871, "Dick's Sporting Goods, Inc."),
    'Cellular Sales': (1097474, 'Cellular Sales of Knoxville, Inc.'),
    'Republic Services': (420392, 'Republic Services, Inc.'),
    'Tenet Healthcare': (1029450, 'Tenet Healthcare Corp.'),
    'LA Fitness': (704021, 'Fitness International LLC'),
    'Brookdale Senior Living': (117838, 'Brookdale Senior Living, Inc.'),
    'AMC Entertainment': (104936, 'AMC Entertainment Holdings, Inc.'),
    'Visiting Angels': (7041939, 'Visiting Angels'),
    'Maverik': (50140, 'Maverik, Inc.'),
    "Trader Joe's": (924576, "Trader Joe's Co., Inc."),
    'MOD Pizza': (5040253, 'MOD Pizza (Cool Dough, LLC)'),
    'Red Wing Shoes': (67862, 'Red Wing Shoe Co., Inc.'),
    "OshKosh B'gosh": (140166, "OshKosh B'gosh, Inc."),
}

brands_to_remove = ["Moe's Southwest Grill", 'TownePlace Suites']

# Remove brands that couldn't be matched
for brand in brands_to_remove:
    mask = matches['brand_name'] == brand
    if mask.sum() > 0:
        old = matches.loc[mask, 'company_name'].values[0]
        locs = matches.loc[mask, 'brand_n_locations'].values[0]
        matches = matches[~mask]
        print(f"REMOVED: {brand} ({locs:,} locs) - was matched to {old}")

# Apply corrections
corrections_applied = 0
for brand_name, (correct_rcid, correct_company_name) in manual_corrections.items():
    mask = matches['brand_name'] == brand_name
    if mask.sum() == 0:
        print(f"WARNING: Brand '{brand_name}' not found in matches")
        continue

    old_company = matches.loc[mask, 'company_name'].values[0]
    old_locs = matches.loc[mask, 'brand_n_locations'].values[0]

    # Look up correct company info
    company_info = companies[companies['rcid'] == correct_rcid]
    if len(company_info) == 0:
        print(f"WARNING: RCID {correct_rcid} not found for {brand_name}")
        continue

    company = company_info.iloc[0]

    # Update match
    matches.loc[mask, 'rcid'] = correct_rcid
    matches.loc[mask, 'company_name'] = correct_company_name
    matches.loc[mask, 'gvkey'] = company['gvkey'] if pd.notna(company['gvkey']) and company['gvkey'] != 'NA' else None
    matches.loc[mask, 'ticker'] = company['ticker'] if pd.notna(company['ticker']) and company['ticker'] != 'NA' else None
    matches.loc[mask, 'company_naics'] = str(company['naics_code']) if pd.notna(company['naics_code']) else None
    matches.loc[mask, 'has_ticker'] = int(company['has_ticker'])
    matches.loc[mask, 'has_gvkey'] = int(company['has_gvkey'])
    matches.loc[mask, 'cosine_similarity'] = 1.0  # Manual match = perfect

    gvkey_str = f" [GVKey:{company['gvkey']}]" if pd.notna(company['gvkey']) and company['gvkey'] != 'NA' else ""
    ticker_str = f" [{company['ticker']}]" if pd.notna(company['ticker']) and company['ticker'] != 'NA' else ""
    id_str = ticker_str or gvkey_str

    print(f"CORRECT: {brand_name} ({old_locs:,} locs)")
    print(f"    OLD: {old_company}")
    print(f"    NEW: {correct_company_name}{id_str}")
    corrections_applied += 1

print(f"\n{'='*60}")
print(f"Applied {corrections_applied} corrections, removed {len(brands_to_remove)} brands")
print(f"Final match count: {len(matches):,}")

# Fix data types before saving
matches['company_naics'] = matches['company_naics'].fillna('').astype(str)
matches['brand_naics'] = matches['brand_naics'].fillna('').astype(str)
matches['gvkey'] = matches['gvkey'].fillna('').astype(str)
matches['ticker'] = matches['ticker'].fillna('').astype(str)

# Replace empty strings with None for cleaner output
matches['company_naics'] = matches['company_naics'].replace('', None)
matches['brand_naics'] = matches['brand_naics'].replace('', None)
matches['gvkey'] = matches['gvkey'].replace('', None)
matches['ticker'] = matches['ticker'].replace('', None)

# Save corrected matches
output_file = INPUT_DIR / 'brand_matches_validated.parquet'
matches.to_parquet(output_file, index=False)
print(f"\nSaved to: {output_file}")

# Summary stats
print(f"\n{'='*60}")
print("Final Summary:")
print(f"{'='*60}")
print(f"  Total matches: {len(matches):,}")
print(f"  Matches with ticker: {matches['has_ticker'].sum():,}")
print(f"  Matches with GVKey: {matches['has_gvkey'].sum():,}")
print(f"  Total locations covered: {matches['brand_n_locations'].sum():,}")
