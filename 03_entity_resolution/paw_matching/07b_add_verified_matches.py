#!/usr/bin/env python3
"""
Add verified borderline matches with correct RCIDs.
"""

import pandas as pd
from pathlib import Path

INPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')

print("Loading data...")
brands = pd.read_parquet(INPUT_DIR / 'advan_brands.parquet')
matches = pd.read_parquet(INPUT_DIR / 'brand_matches_validated.parquet')
companies = pd.read_parquet(INPUT_DIR / 'paw_companies_for_matching.parquet')

matched_brand_ids = set(matches['safegraph_brand_id'])
unmatched = brands[~brands['safegraph_brand_id'].isin(matched_brand_ids)].copy()

print(f"Current matches: {len(matches):,}")
print(f"Unmatched brands: {len(unmatched):,}")

# Verified matches: brand_name -> rcid
verified_matches = {
    # Borderline matches (0.75-0.78) with clear name overlap
    'Do It Best': 1054726,  # Do it Best Corp.
    'ULTA Beauty': 1035037,  # Ulta Beauty, Inc. [ULTA]
    'Quick Lane': 11944906,  # Quick Lane Tire & Auto Center
    'Athletico Physical Therapy': 414831,  # Athletico Ltd.
    'El Pollo Loco': 22148144,  # El Pollo Loco Holdings, Inc. [LOCO]
    'Geico': 646638,  # GEICO Corp.
    '9Round': 765872,  # 9Round Franchising LLC
    'The Habit Burger Grill': 49797449,  # The Habit Restaurants LLC
    'Super 8': 1145613,  # Super 8 Motel, Inc.
    'Regus': 261051,  # Regus Plc SA
    'maurices': 1095558,  # Maurices, Inc.
    'Bealls Outlet': 588598,  # Beall's Outlet Stores, Inc.
    'Les Schwab': 14589713,  # Les Schwab Tire Centers of Oregon LLC
    'Pilot Flying J': 283439,  # Pilot Travel Centers LLC
    'Cost Cutters': 2933737,  # Cost Cutters Hair Salon

    # Large unmatched brands
    'Progressive': 744201,  # Progressive Corp. [PGR]
    'Sonic': 653848,  # Sonic Corp.
    'Hertz': 914117,  # The Hertz Corp.
    '7-Eleven Fuel': 824957,  # 7-Eleven, Inc.
    'U.S. Bank ATM': 449435,  # U.S. Bancorp [USB]
    'Bank of America ATM': 393528,  # Bank of America Corp. [BAC]
    'Chase ATM': 543448,  # JPMorgan Chase & Co. [JPM]
    'PNC Financial Services ATM': 22142569,  # The PNC Financial Services Group, Inc. [PNC]
    'BBVA ATM': 420470,  # BBVA USA
    'Kia Motors': 1209767,  # Kia Corp.
    'FedEx Drop Box': 806872,  # FedEx Corp. [FDX]
    'UPS Drop Box': 22142761,  # United Parcel Service, Inc. [UPS]
    'DHL Service Point': 963400,  # DHL Express (USA), Inc.
    'Ria Money Transfer Partner Location': 919316,  # RIA Money Transfer, Inc.
    'NCR Pay360': 1008117,  # NCR Voyix Corp. [VYX]
    'Walmart Photo Center': 22142783,  # Walmart, Inc. [WMT]
    'Keyme Kiosk': 561445,  # KeyMe LLC
    'Tesla Destination Charger': 606259,  # Tesla Energy Operations, Inc.
    'Tesla Supercharger': 606259,  # Tesla Energy Operations, Inc.
    'USPS Collection Point': 7393735,  # United States Postal Service
    'Umpqua Bank': 954578,  # Umpqua Bank
    'Winnebago Dealer': 692895,  # Winnebago Industries, Inc. [WGO]
    'Comerica Bank ATM': 337515,  # Comerica, Inc. [CMA]
    'Cicis': 382035,  # CiCi Enterprises LP
    'Cash America': 625464,  # Cash America International, Inc.
}

print(f"\n{'='*70}")
print(f"ADDING {len(verified_matches)} VERIFIED MATCHES")
print("=" * 70)

new_matches = []
for brand_name, rcid in verified_matches.items():
    # Get brand info
    brand_row = unmatched[unmatched['brand_name'] == brand_name]
    if len(brand_row) == 0:
        print(f"SKIP: {brand_name} - already matched or not found")
        continue

    brand_info = brand_row.iloc[0]

    # Get company info
    company_row = companies[companies['rcid'] == rcid]
    if len(company_row) == 0:
        print(f"ERROR: RCID {rcid} not found for {brand_name}")
        continue

    company = company_row.iloc[0]

    # Create match record
    match = {
        'safegraph_brand_id': brand_info['safegraph_brand_id'],
        'brand_name': brand_name,
        'brand_n_locations': int(brand_info['n_locations']),
        'brand_naics': str(int(brand_info['naics_code'])) if pd.notna(brand_info['naics_code']) else None,
        'rcid': rcid,
        'company_name': company['company_name'],
        'gvkey': company['gvkey'] if pd.notna(company['gvkey']) and company['gvkey'] != 'NA' else None,
        'ticker': company['ticker'] if pd.notna(company['ticker']) and company['ticker'] != 'NA' else None,
        'company_naics': str(company['naics_code']) if pd.notna(company['naics_code']) else None,
        'has_ticker': int(company['has_ticker']),
        'has_gvkey': int(company['has_gvkey']),
        'cosine_similarity': 1.0,  # Manual match
    }

    new_matches.append(match)

    gvkey_str = f" [GVKey:{company['gvkey']}]" if company['has_gvkey'] else ""
    ticker_str = f" [{company['ticker']}]" if company['has_ticker'] else ""
    id_str = ticker_str or gvkey_str
    print(f"ADD: {brand_name} ({brand_info['n_locations']:,} locs) -> {company['company_name']}{id_str}")

print(f"\n{'='*70}")
print(f"Adding {len(new_matches)} new matches")
print("=" * 70)

# Combine with existing matches
if new_matches:
    new_df = pd.DataFrame(new_matches)
    combined = pd.concat([matches, new_df], ignore_index=True)

    # Fix data types
    combined['company_naics'] = combined['company_naics'].fillna('').astype(str).replace('', None)
    combined['brand_naics'] = combined['brand_naics'].fillna('').astype(str).replace('', None)
    combined['gvkey'] = combined['gvkey'].fillna('').astype(str).replace('', None)
    combined['ticker'] = combined['ticker'].fillna('').astype(str).replace('', None)

    # Save
    output_file = INPUT_DIR / 'brand_matches_validated.parquet'
    combined.to_parquet(output_file, index=False)

    print(f"\nSaved to: {output_file}")
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Previous matches: {len(matches):,}")
    print(f"  New matches added: {len(new_matches)}")
    print(f"  Total matches: {len(combined):,}")
    print(f"  Matches with ticker: {combined['has_ticker'].sum():,}")
    print(f"  Matches with GVKey: {combined['has_gvkey'].sum():,}")
    print(f"  Total locations covered: {combined['brand_n_locations'].sum():,}")

    # Show biggest additions
    print(f"\n{'='*70}")
    print("TOP 10 NEW MATCHES BY LOCATION COUNT")
    print("=" * 70)
    new_df_sorted = new_df.sort_values('brand_n_locations', ascending=False).head(10)
    for _, row in new_df_sorted.iterrows():
        print(f"  {row['brand_name']}: {row['brand_n_locations']:,} locations -> {row['company_name']}")
else:
    print("No new matches to add")
