#!/usr/bin/env python3
"""
Step 1: Extract unique entities for matching.
- Unique Advan brands (from US POIs)
- Unique PAW companies with tickers
- Unique PAW companies by MSA
"""

import duckdb
from pathlib import Path

US_POI_FILE = Path('/global/scratch/users/maxkagan/project_oakland/inputs/entity_resolution/advan_pois_us_only.parquet')
BRAND_INFO_FILE = Path('/global/scratch/users/maxkagan/01_foot_traffic_location/advan/brand_info/Brand_Info_Places_Patterns_Geometry_Spend_-0.csv')
PAW_CROSSWALK = Path('/global/scratch/users/maxkagan/04_labor_workforce/revelio_20250416/company_crosswalk/company_crosswalk.parquet')
PAW_POSITIONS_DIR = Path('/global/scratch/users/maxkagan/04_labor_workforce/merge_splink_fuzzylink/step11_company_enriched')

OUTPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/inputs/entity_resolution')

def extract_advan_brands(con):
    """Extract unique branded POIs from US data, joined with brand info."""
    print("\n" + "=" * 60)
    print("Extracting unique Advan brands from US POIs...")
    print("=" * 60)

    output_file = OUTPUT_DIR / 'advan_brands_unique.parquet'

    query = f"""
    COPY (
        SELECT DISTINCT
            p.SAFEGRAPH_BRAND_IDS as safegraph_brand_id,
            p.BRANDS as brand_name_from_poi,
            b.BRAND_NAME as brand_name,
            b.STOCK_SYMBOL as stock_symbol,
            b.STOCK_EXCHANGE as stock_exchange,
            b.NAICS_CODE as naics_code,
            b.TOP_CATEGORY as top_category,
            b.SUB_CATEGORY as sub_category,
            b.PARENT_SAFEGRAPH_BRAND_ID as parent_brand_id
        FROM parquet_scan('{US_POI_FILE}') p
        LEFT JOIN read_csv_auto('{BRAND_INFO_FILE}') b
            ON p.SAFEGRAPH_BRAND_IDS = b.SAFEGRAPH_BRAND_ID
        WHERE p.SAFEGRAPH_BRAND_IDS IS NOT NULL
        AND p.SAFEGRAPH_BRAND_IDS != ''
    ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    con.execute(query)

    result = con.execute(f"SELECT COUNT(*) FROM parquet_scan('{output_file}')").fetchone()
    with_ticker = con.execute(f"""
        SELECT COUNT(*) FROM parquet_scan('{output_file}')
        WHERE stock_symbol IS NOT NULL AND stock_symbol != ''
    """).fetchone()

    print(f"  Unique brands in US: {result[0]:,}")
    print(f"  Brands with stock symbol: {with_ticker[0]:,}")
    print(f"  Output: {output_file}")

    return output_file

def extract_paw_companies_with_ticker(con):
    """Extract PAW companies that have tickers (for exact matching)."""
    print("\n" + "=" * 60)
    print("Extracting PAW companies with tickers...")
    print("=" * 60)

    output_file = OUTPUT_DIR / 'paw_companies_with_ticker.parquet'

    query = f"""
    COPY (
        SELECT DISTINCT
            rcid,
            company_name,
            ticker,
            naics_code,
            naics_description,
            city,
            state,
            country,
            ultimate_parent_rcid,
            ultimate_parent_company_name
        FROM parquet_scan('{PAW_CROSSWALK}')
        WHERE ticker IS NOT NULL
        AND ticker != ''
        AND country = 'United States'
    ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    con.execute(query)

    result = con.execute(f"SELECT COUNT(*) FROM parquet_scan('{output_file}')").fetchone()
    print(f"  PAW companies with tickers: {result[0]:,}")
    print(f"  Output: {output_file}")

    return output_file

def extract_paw_companies_all_unique(con):
    """Extract all unique PAW company names (for fuzzy matching)."""
    print("\n" + "=" * 60)
    print("Extracting all unique PAW companies...")
    print("=" * 60)

    output_file = OUTPUT_DIR / 'paw_companies_unique.parquet'

    query = f"""
    COPY (
        SELECT DISTINCT
            rcid,
            company_name,
            ticker,
            naics_code,
            naics_description,
            city,
            state,
            country,
            ultimate_parent_rcid,
            ultimate_parent_company_name
        FROM parquet_scan('{PAW_CROSSWALK}')
        WHERE country = 'United States'
        AND company_name IS NOT NULL
        AND company_name != ''
    ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    con.execute(query)

    result = con.execute(f"SELECT COUNT(*) FROM parquet_scan('{output_file}')").fetchone()
    print(f"  Unique US PAW companies: {result[0]:,}")
    print(f"  Output: {output_file}")

    return output_file

def count_paw_companies_by_msa(con):
    """Count unique PAW companies per MSA (for Tier 2 planning)."""
    print("\n" + "=" * 60)
    print("Counting PAW companies by MSA...")
    print("=" * 60)

    msa_files = list(PAW_POSITIONS_DIR.glob('*_positions.parquet'))
    print(f"  Found {len(msa_files)} MSA position files")

    msa_counts = []
    for msa_file in sorted(msa_files)[:5]:
        msa_name = msa_file.stem.replace('_positions', '')
        try:
            count = con.execute(f"""
                SELECT COUNT(DISTINCT pos_company_name)
                FROM parquet_scan('{msa_file}')
                WHERE pos_company_name IS NOT NULL
            """).fetchone()[0]
            msa_counts.append((msa_name, count))
            print(f"    {msa_name}: {count:,} unique companies")
        except Exception as e:
            print(f"    {msa_name}: ERROR - {e}")

    print(f"\n  (Showing 5 of {len(msa_files)} MSAs)")

def main():
    print("=" * 60)
    print("Step 1: Extract Unique Entities")
    print("=" * 60)

    if not US_POI_FILE.exists():
        raise FileNotFoundError(f"US POI file not found: {US_POI_FILE}\nRun Step 0 first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("SET threads TO 32")
    con.execute("SET memory_limit = '80GB'")

    extract_advan_brands(con)
    extract_paw_companies_with_ticker(con)
    extract_paw_companies_all_unique(con)
    count_paw_companies_by_msa(con)

    con.close()
    print("\n" + "=" * 60)
    print("Step 1 complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
