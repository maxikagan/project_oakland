#!/usr/bin/env python3
"""
Step 0: Filter Advan POI data to US-only (50 states + DC).
Excludes US territories (PR, VI, GU, AS, MP).
"""

import duckdb
from pathlib import Path

INPUT_DIR = Path('/global/scratch/users/maxkagan/01_foot_traffic_location/safegraph/poi_data_dewey_10_21_2024')
OUTPUT_FILE = Path('/global/scratch/users/maxkagan/project_oakland/inputs/entity_resolution/advan_pois_us_only.parquet')

US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL',
    'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE',
    'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD',
    'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

def main():
    print("=" * 60)
    print("Step 0: Filter Advan POIs to US-only")
    print("=" * 60)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    csv_files = list(INPUT_DIR.glob('*.csv.gz'))
    if len(csv_files) == 0:
        raise FileNotFoundError(f"No .csv.gz files found in {INPUT_DIR}")
    print(f"Found {len(csv_files)} CSV files to process")

    con = duckdb.connect()
    con.execute("SET threads TO 24")
    con.execute("SET memory_limit = '50GB'")

    states_list = ', '.join([f"'{s}'" for s in US_STATES])

    query = f"""
    COPY (
        SELECT *
        FROM read_csv_auto('{INPUT_DIR}/*.csv.gz', compression='gzip', header=true, union_by_name=true)
        WHERE ISO_COUNTRY_CODE = 'US'
        AND REGION IN ({states_list})
    ) TO '{OUTPUT_FILE}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    print("Filtering to US states only (excluding territories)...")
    print(f"Output: {OUTPUT_FILE}")

    con.execute(query)

    result = con.execute(f"SELECT COUNT(*) FROM parquet_scan('{OUTPUT_FILE}')").fetchone()
    if result[0] == 0:
        raise ValueError("No POIs matched filter criteria - check column values")
    print(f"\nFiltered POI count: {result[0]:,}")

    schema = con.execute(f"DESCRIBE SELECT * FROM parquet_scan('{OUTPUT_FILE}')").fetchall()
    print(f"\nSchema ({len(schema)} columns):")
    for col in schema[:10]:
        print(f"  {col[0]}: {col[1]}")
    if len(schema) > 10:
        print(f"  ... and {len(schema) - 10} more columns")

    branded = con.execute(f"""
        SELECT COUNT(*) FROM parquet_scan('{OUTPUT_FILE}')
        WHERE SAFEGRAPH_BRAND_IDS IS NOT NULL AND SAFEGRAPH_BRAND_IDS != ''
    """).fetchone()

    singletons = result[0] - branded[0]
    print(f"\nBreakdown:")
    print(f"  Branded POIs: {branded[0]:,}")
    print(f"  Singletons: {singletons:,}")

    con.close()
    print("\nDone!")

if __name__ == '__main__':
    main()
