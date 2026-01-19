#!/usr/bin/env python3
"""
Add valid borderline matches (0.75-0.78 similarity) that have clear name overlap.
Also search for correct matches for large brands with wrong automatic matches.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

INPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')
CACHE_DIR = INPUT_DIR / 'embedding_cache'

print("Loading data...")
brands = pd.read_parquet(INPUT_DIR / 'advan_brands.parquet')
matches = pd.read_parquet(INPUT_DIR / 'brand_matches_validated.parquet')
companies = pd.read_parquet(INPUT_DIR / 'paw_companies_for_matching.parquet')

matched_brand_ids = set(matches['safegraph_brand_id'])
unmatched = brands[~brands['safegraph_brand_id'].isin(matched_brand_ids)].copy()

print(f"Current matches: {len(matches):,}")
print(f"Unmatched brands: {len(unmatched):,}")
print(f"Companies available: {len(companies):,}")

# Helper function to search companies
def search_companies(query, top_n=5):
    """Search companies by name substring."""
    mask = companies['company_name'].str.contains(query, case=False, na=False)
    results = companies[mask].copy()
    results = results.sort_values('has_gvkey', ascending=False).head(top_n)
    return results[['rcid', 'company_name', 'gvkey', 'ticker', 'has_gvkey', 'has_ticker']]

# Manual matches for borderline brands with clear name overlap
# Format: brand_name -> (search_query, expected_company_substring)
borderline_matches_to_verify = {
    # From 0.75-0.78 range with clear name overlap
    'Do It Best': 'Do it Best',
    'ULTA Beauty': 'Ulta Beauty',
    'Quick Lane': 'Quick Lane',
    'Athletico Physical Therapy': 'Athletico',
    'El Pollo Loco': 'El Pollo Loco',
    'Geico': 'GEICO',
    '9Round': '9Round',
    'The Habit Burger Grill': 'Habit',
    'Super 8': 'Super 8',
    'Regus': 'Regus',
    'maurices': 'Maurices',
    'Bealls Outlet': 'Bealls',
    'Les Schwab': 'Les Schwab',
    'Sign-A-Rama': 'Sign-A-Rama',
    'Senior Helpers': 'Senior Helpers',
    'Courtyard by Marriott': 'Marriott',
    'Pilot Flying J': 'Pilot',
    'Cost Cutters': 'Cost Cutters',
    'Comerica Bank ATM': 'Comerica',

    # Large unmatched brands that need correct company
    'Progressive': 'Progressive Corporation',
    'Shell Oil': 'Shell',
    'Sonic': 'Sonic Corp',
    'Hertz': 'Hertz Corp',
    '7-Eleven Fuel': '7-Eleven',
    'Volta Charging': 'Volta',
    'U.S. Bank ATM': 'U.S. Bank',
    'Bank of America ATM': 'Bank of America',
    'Chase ATM': 'JPMorgan Chase',
    'PNC Financial Services ATM': 'PNC',
    'BBVA ATM': 'BBVA',
    'Kia Motors': 'Kia',
    'FedEx Drop Box': 'FedEx',
    'UPS Drop Box': 'United Parcel',
    'DHL Service Point': 'DHL',
    'Ria Money Transfer Partner Location': 'Ria',
    'NCR Pay360': 'NCR',
    'Walmart Photo Center': 'Walmart',
    'Crypto Dispensers': None,  # Skip - not a real company match
    'Health Street': 'Health Street',
    'Keyme Kiosk': 'KeyMe',
    'Tesla Destination Charger': 'Tesla',
    'Tesla Supercharger': 'Tesla',
    'CoinFlip Bitcoin ATM': 'CoinFlip',
    'Bitcoin Depot Bitcoin ATM': 'Bitcoin Depot',
    'USPS Collection Point': 'Postal Service',
    'Cicis': "Cici's Pizza",
    'Umpqua Bank': 'Umpqua',
    'Family Video': 'Family Video',
    'Cash America': 'Cash America',
    'Winnebago Dealer': 'Winnebago',
}

print("\n" + "=" * 70)
print("SEARCHING FOR CORRECT COMPANY MATCHES")
print("=" * 70)

# Store verified matches
verified_matches = []

for brand_name, search_query in borderline_matches_to_verify.items():
    if search_query is None:
        print(f"\n{brand_name}: SKIPPED (no valid company match)")
        continue

    # Get brand info
    brand_row = unmatched[unmatched['brand_name'] == brand_name]
    if len(brand_row) == 0:
        print(f"\n{brand_name}: Already matched or not found")
        continue

    brand_info = brand_row.iloc[0]

    # Search for company
    results = search_companies(search_query)

    print(f"\n{brand_name} ({brand_info['n_locations']:,} locs) - searching '{search_query}':")

    if len(results) == 0:
        print("  No results found")
        continue

    for _, company in results.iterrows():
        gvkey_str = f" [GVKey:{company['gvkey']}]" if company['has_gvkey'] else ""
        ticker_str = f" [{company['ticker']}]" if company['has_ticker'] else ""
        id_str = ticker_str or gvkey_str
        print(f"  RCID {company['rcid']}: {company['company_name']}{id_str}")

print("\n" + "=" * 70)
print("MANUAL MATCH SELECTIONS")
print("=" * 70)

# Based on search results, define the correct matches
# Format: brand_name -> (rcid, company_name) or None to skip
manual_selections = {
    # Borderline with clear name match
    'Do It Best': (598648, 'Do it Best Corp.'),
    'ULTA Beauty': (934935, 'Ulta Beauty, Inc.'),
    'Quick Lane': (1058629, 'Quick Lane Tire & Auto Center'),
    'Athletico Physical Therapy': (362529, 'Athletico Management LLC'),
    'El Pollo Loco': (633081, 'El Pollo Loco Holdings, Inc.'),
    'Geico': (773839, 'GEICO Corp.'),
    '9Round': (7936, '9Round Franchising LLC'),
    'The Habit Burger Grill': (1174992, 'The Habit Restaurants LLC'),
    'Super 8': (1136908, 'Super 8 Worldwide, Inc.'),
    'Regus': (879893, 'Regus Management Group LLC'),
    'maurices': (754566, "Maurices, Inc."),
    'Bealls Outlet': (249685, 'Beall\'s, Inc.'),
    'Les Schwab': (709276, 'Les Schwab Tire Centers of Oregon, Inc.'),
    'Pilot Flying J': (1037251, 'Pilot Travel Centers LLC'),
    'Cost Cutters': (552880, 'Cost Cutters Family Hair Care'),

    # Large brands needing correct company
    'Progressive': (848550, 'Progressive Corporation'),
    'Shell Oil': (912348, 'Exxon Mobil Corp.'),  # Shell is part of ExxonMobil in US retail
    'Sonic': (1064612, 'Sonic Corp.'),
    'Hertz': (1212247, 'The Hertz Corp.'),
    '7-Eleven Fuel': (2424, '7-Eleven, Inc.'),
    'Volta Charging': (7092568, 'Volta, Inc.'),
    'U.S. Bank ATM': (961315, 'U.S. Bancorp'),
    'Bank of America ATM': (240714, 'Bank of America Corp.'),
    'Chase ATM': (679285, 'JPMorgan Chase & Co.'),
    'PNC Financial Services ATM': (843051, 'The PNC Financial Services Group, Inc.'),
    'BBVA ATM': (252295, 'BBVA USA'),
    'Kia Motors': (687624, 'Kia America, Inc.'),
    'FedEx Drop Box': (684037, 'FedEx Corp.'),
    'UPS Drop Box': (948960, 'United Parcel Service, Inc.'),
    'DHL Service Point': (597858, 'DHL Express (USA), Inc.'),
    'Ria Money Transfer Partner Location': (879233, 'Ria Financial Services, Inc.'),
    'NCR Pay360': (790688, 'NCR Voyix Corp.'),
    'Walmart Photo Center': (1340178, 'Walmart, Inc.'),
    'Health Street': (789286, 'Health Street, Inc.'),
    'Keyme Kiosk': (686855, 'KeyMe LLC'),
    'Tesla Destination Charger': (1177206, 'Tesla, Inc.'),
    'Tesla Supercharger': (1177206, 'Tesla, Inc.'),
    'USPS Collection Point': (949266, 'United States Postal Service'),
    'Umpqua Bank': (942545, 'Umpqua Holdings Corp.'),
    'Winnebago Dealer': (986296, 'Winnebago Industries, Inc.'),
    'Comerica Bank ATM': (530009, 'Comerica, Inc.'),

    # These need more research - skip for now
    'Sign-A-Rama': None,  # Franchise, no clear parent
    'Senior Helpers': None,  # Franchise, no clear parent
    'Courtyard by Marriott': None,  # Would duplicate Marriott match
    'CoinFlip Bitcoin ATM': None,  # Crypto ATM network
    'Bitcoin Depot Bitcoin ATM': None,  # Crypto ATM network
    'Cicis': None,  # Need to verify
    'Family Video': None,  # Defunct
    'Cash America': None,  # Need to verify
    'Crypto Dispensers': None,  # Not a real company
}

# Now apply the selections
new_matches = []

for brand_name, selection in manual_selections.items():
    if selection is None:
        continue

    rcid, expected_company_name = selection

    # Get brand info
    brand_row = unmatched[unmatched['brand_name'] == brand_name]
    if len(brand_row) == 0:
        continue

    brand_info = brand_row.iloc[0]

    # Get company info
    company_row = companies[companies['rcid'] == rcid]
    if len(company_row) == 0:
        print(f"WARNING: RCID {rcid} not found for {brand_name}")
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
print(f"{'='*70}")

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
    print(f"\nFinal Summary:")
    print(f"  Previous matches: {len(matches):,}")
    print(f"  New matches added: {len(new_matches)}")
    print(f"  Total matches: {len(combined):,}")
    print(f"  Matches with ticker: {combined['has_ticker'].sum():,}")
    print(f"  Matches with GVKey: {combined['has_gvkey'].sum():,}")
    print(f"  Total locations covered: {combined['brand_n_locations'].sum():,}")
else:
    print("No new matches to add")
