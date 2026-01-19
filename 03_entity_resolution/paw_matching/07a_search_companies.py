#!/usr/bin/env python3
"""
Search for correct company matches for borderline brands.
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

print(f"Companies available: {len(companies):,}")

def search_companies(query, top_n=8):
    """Search companies by name substring."""
    mask = companies['company_name'].str.contains(query, case=False, na=False, regex=False)
    results = companies[mask].copy()
    # Prioritize those with GVKey/ticker
    results = results.sort_values(['has_gvkey', 'has_ticker'], ascending=False).head(top_n)
    return results[['rcid', 'company_name', 'gvkey', 'ticker', 'has_gvkey', 'has_ticker']]

# Brands to search for
searches = [
    ('Do It Best', 'Do it Best'),
    ('ULTA Beauty', 'Ulta Beauty'),
    ('Quick Lane', 'Quick Lane'),
    ('Athletico Physical Therapy', 'Athletico'),
    ('El Pollo Loco', 'El Pollo Loco'),
    ('Geico', 'GEICO'),
    ('9Round', '9Round'),
    ('The Habit Burger Grill', 'Habit Restaurant'),
    ('Super 8', 'Super 8'),
    ('Regus', 'Regus'),
    ('maurices', 'Maurice'),
    ('Bealls Outlet', 'Beall'),
    ('Les Schwab', 'Les Schwab'),
    ('Pilot Flying J', 'Pilot Travel'),
    ('Cost Cutters', 'Cost Cutter'),
    ('Progressive', 'Progressive Corp'),
    ('Shell Oil', 'Shell Oil'),
    ('Sonic', 'Sonic Corp'),
    ('Hertz', 'Hertz Corp'),
    ('7-Eleven Fuel', '7-Eleven'),
    ('Volta Charging', 'Volta'),
    ('U.S. Bank ATM', 'U.S. Bancorp'),
    ('Bank of America ATM', 'Bank of America Corp'),
    ('Chase ATM', 'JPMorgan Chase'),
    ('PNC Financial Services ATM', 'PNC Financial'),
    ('BBVA ATM', 'BBVA'),
    ('Kia Motors', 'Kia'),
    ('FedEx Drop Box', 'FedEx Corp'),
    ('UPS Drop Box', 'United Parcel'),
    ('DHL Service Point', 'DHL Express'),
    ('Ria Money Transfer Partner Location', 'Ria Financial'),
    ('NCR Pay360', 'NCR'),
    ('Walmart Photo Center', 'Walmart Inc'),
    ('Health Street', 'Health Street'),
    ('Keyme Kiosk', 'KeyMe'),
    ('Tesla Destination Charger', 'Tesla Inc'),
    ('USPS Collection Point', 'Postal Service'),
    ('Umpqua Bank', 'Umpqua'),
    ('Winnebago Dealer', 'Winnebago'),
    ('Comerica Bank ATM', 'Comerica'),
    ('Cicis', "Cici"),
    ('Family Video', 'Family Video'),
    ('Cash America', 'Cash America'),
]

for brand_name, search_query in searches:
    # Get brand info
    brand_row = unmatched[unmatched['brand_name'] == brand_name]
    if len(brand_row) == 0:
        locs = "Already matched"
    else:
        locs = f"{brand_row.iloc[0]['n_locations']:,} locs"

    print(f"\n{'='*70}")
    print(f"{brand_name} ({locs}) - searching '{search_query}':")
    print("=" * 70)

    results = search_companies(search_query)

    if len(results) == 0:
        print("  No results found")
        continue

    for _, company in results.iterrows():
        gvkey_str = f" [GVKey:{company['gvkey']}]" if company['has_gvkey'] else ""
        ticker_str = f" [{company['ticker']}]" if company['has_ticker'] else ""
        id_str = ticker_str or gvkey_str
        print(f"  RCID {company['rcid']:>8}: {company['company_name']}{id_str}")
