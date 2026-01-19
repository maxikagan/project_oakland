#!/usr/bin/env python3
"""
Step 2: Extract unique brands from Advan and PAW for matching.

Since the Brand Info file with STOCK_SYMBOL is not available,
we extract brand names directly and will match using embeddings.

Outputs:
- advan_brands.parquet: Unique Advan brands with location counts
- paw_companies_for_matching.parquet: PAW companies (prioritizing those with tickers)
"""

import sys
print("Starting Python script...", flush=True)

import duckdb
print("Imported duckdb", flush=True)
from pathlib import Path
print("Imports complete", flush=True)

US_POI_FILE = Path('/global/scratch/users/maxkagan/project_oakland/inputs/entity_resolution/advan_pois_us_only.parquet')
PAW_VR_SCORES = Path('/global/scratch/users/maxkagan/04_vrscores/merge_splink_fuzzylink/vr_scores_ensemble_additional_gvkeys.csv')
OUTPUT_DIR = Path('/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution')


def extract_advan_brands(con):
    """Extract unique Advan brands with location counts and categories."""
    print("\n" + "=" * 60)
    print("Extracting unique Advan brands...")
    print("=" * 60)

    output_file = OUTPUT_DIR / 'advan_brands.parquet'

    query = f"""
    COPY (
        SELECT
            SAFEGRAPH_BRAND_IDS as safegraph_brand_id,
            BRANDS as brand_name,
            COUNT(*) as n_locations,
            MODE(TOP_CATEGORY) as top_category,
            MODE(SUB_CATEGORY) as sub_category,
            MODE(NAICS_CODE) as naics_code,
            COUNT(DISTINCT REGION) as n_states,
            COUNT(DISTINCT CITY) as n_cities
        FROM parquet_scan('{US_POI_FILE}')
        WHERE SAFEGRAPH_BRAND_IDS IS NOT NULL
        AND SAFEGRAPH_BRAND_IDS != ''
        GROUP BY SAFEGRAPH_BRAND_IDS, BRANDS
        ORDER BY n_locations DESC
    ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    con.execute(query)

    stats = con.execute(f"""
        SELECT
            COUNT(*) as n_brands,
            SUM(n_locations) as total_locations,
            AVG(n_locations) as avg_locations
        FROM parquet_scan('{output_file}')
    """).fetchone()

    print(f"  Unique brands: {stats[0]:,}")
    print(f"  Total branded locations: {stats[1]:,}")
    print(f"  Avg locations per brand: {stats[2]:.1f}")
    print(f"  Output: {output_file}")

    return output_file


def extract_paw_companies(con):
    """Extract PAW companies for matching from VR scores file."""
    print("\n" + "=" * 60)
    print("Extracting PAW companies for matching...")
    print("=" * 60)

    output_file = OUTPUT_DIR / 'paw_companies_for_matching.parquet'

    query = f"""
    COPY (
        SELECT
            rcid,
            company_name,
            final_parent_company,
            final_parent_company_rcid,
            gvkey,
            ticker,
            exchange,
            factset_entity_id,
            cusip,
            naics_code,
            naics_desc as naics_description,
            modal_state as state,
            modal_city as city,
            modal_msa as msa,
            CASE WHEN ticker IS NOT NULL AND ticker != '' AND ticker != 'NA' THEN 1 ELSE 0 END as has_ticker,
            CASE WHEN gvkey IS NOT NULL AND gvkey != '' AND gvkey != 'NA' THEN 1 ELSE 0 END as has_gvkey
        FROM read_csv('{PAW_VR_SCORES}', AUTO_DETECT=TRUE, nullstr='NA')
        WHERE company_name IS NOT NULL
        AND company_name != ''
        -- Deduplicate by company_name, keeping the one with ticker/gvkey if available
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY LOWER(TRIM(company_name))
            ORDER BY
                CASE WHEN ticker IS NOT NULL AND ticker != '' AND ticker != 'NA' THEN 0 ELSE 1 END,
                CASE WHEN gvkey IS NOT NULL AND gvkey != '' AND gvkey != 'NA' THEN 0 ELSE 1 END,
                rcid
        ) = 1
    ) TO '{output_file}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    con.execute(query)

    stats = con.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(has_ticker) as with_ticker,
            SUM(has_gvkey) as with_gvkey
        FROM parquet_scan('{output_file}')
    """).fetchone()

    print(f"  Total unique companies: {stats[0]:,}")
    print(f"  Companies with tickers: {stats[1]:,}")
    print(f"  Companies with GVKeys: {stats[2]:,}")
    print(f"  Output: {output_file}")

    return output_file


def main():
    print("=" * 60)
    print("Step 2: Extract Brands and Companies for Matching")
    print("=" * 60)

    if not US_POI_FILE.exists():
        raise FileNotFoundError(f"US POI file not found: {US_POI_FILE}\nRun Step 0 first.")

    if not PAW_VR_SCORES.exists():
        raise FileNotFoundError(f"PAW VR scores file not found: {PAW_VR_SCORES}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("SET threads TO 32")
    con.execute("SET memory_limit = '80GB'")

    extract_advan_brands(con)
    extract_paw_companies(con)

    con.close()

    print("\n" + "=" * 60)
    print("Step 2 complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
