#!/usr/bin/env python3
"""
Task 1.5: Aggregate POI-month partisan lean to brand-month level.

Methodology:
    brand_lean = Σ(rep_lean_i × normalized_visits_i) / Σ(normalized_visits_i)

Filters:
    - pct_visitors_matched >= 0.95 (95% threshold - keeps 99.5% of data)
    - Only brands matched in entity resolution (3,912 brands)

Output:
    Single parquet file with brand × month rows containing:
    - Brand identifiers (safegraph_brand_id, brand_name, brand_n_locations, brand_naics)
    - Company identifiers (rcid, company_name, gvkey, ticker, company_naics)
    - Partisan lean scores (brand_lean_2020, brand_lean_2016)
    - Aggregation metadata (n_pois, total_normalized_visits, n_states, n_cbsas)
    - Category info (top_category, sub_category, naics_code - mode across POIs)
"""

import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

# Paths
INPUT_DIR = Path('/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national_with_normalized')
ENTITY_RESOLUTION_PATH = Path('/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/entity_resolution/brand_matches_validated.parquet')
OUTPUT_DIR = Path('/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/brand_month_aggregated')

# Filter thresholds
MIN_PCT_VISITORS_MATCHED = 0.95


def get_mode(values):
    """Return most common value from a list, or None if empty."""
    if not values:
        return None
    # Filter out None/NaN values
    clean_values = [v for v in values if v is not None and (not isinstance(v, float) or not pd.isna(v))]
    if not clean_values:
        return None
    counts = Counter(clean_values)
    return counts.most_common(1)[0][0]


def aggregate_single_month(df: pd.DataFrame, brand_lookup: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate POI-month data to brand-month level for a single month.

    Args:
        df: POI-month dataframe with partisan lean data
        brand_lookup: Entity resolution dataframe mapping brand -> company info

    Returns:
        Brand-month aggregated dataframe
    """
    # Filter by pct_visitors_matched threshold
    df = df[df['pct_visitors_matched'] >= MIN_PCT_VISITORS_MATCHED].copy()

    # Filter to branded POIs only
    df = df[df['brand'].notna()].copy()

    if df.empty:
        return pd.DataFrame()

    # Join to entity resolution (inner join keeps only matched brands)
    df = df.merge(brand_lookup, left_on='brand', right_on='brand_name', how='inner')

    if df.empty:
        return pd.DataFrame()

    # Compute weighted components
    df['weighted_lean_2020'] = df['rep_lean_2020'] * df['normalized_visits_by_state_scaling']
    df['weighted_lean_2016'] = df['rep_lean_2016'] * df['normalized_visits_by_state_scaling']

    # Aggregate by brand
    agg = df.groupby('brand_name').agg(
        sum_weighted_lean_2020=('weighted_lean_2020', 'sum'),
        sum_weighted_lean_2016=('weighted_lean_2016', 'sum'),
        total_normalized_visits=('normalized_visits_by_state_scaling', 'sum'),
        n_pois=('placekey', 'nunique'),
        n_states=('region', 'nunique'),
        n_cbsas=('cbsa_title', 'nunique'),
        top_category_list=('top_category', list),
        sub_category_list=('sub_category', list),
        naics_code_list=('naics_code', list),
        year_month=('year_month', 'first'),
        # Entity resolution fields (constant per brand)
        safegraph_brand_id=('safegraph_brand_id', 'first'),
        brand_n_locations=('brand_n_locations', 'first'),
        brand_naics=('brand_naics', 'first'),
        rcid=('rcid', 'first'),
        company_name=('company_name', 'first'),
        gvkey=('gvkey', 'first'),
        ticker=('ticker', 'first'),
        company_naics=('company_naics', 'first'),
    ).reset_index()

    # Compute weighted averages
    agg['brand_lean_2020'] = agg['sum_weighted_lean_2020'] / agg['total_normalized_visits']
    agg['brand_lean_2016'] = agg['sum_weighted_lean_2016'] / agg['total_normalized_visits']

    # Get mode for categorical columns
    agg['top_category'] = agg['top_category_list'].apply(get_mode)
    agg['sub_category'] = agg['sub_category_list'].apply(get_mode)
    agg['naics_code'] = agg['naics_code_list'].apply(get_mode)

    # Select and order output columns
    output_cols = [
        # Brand identifiers
        'safegraph_brand_id',
        'brand_name',
        'brand_n_locations',
        'brand_naics',
        # Company identifiers
        'rcid',
        'company_name',
        'gvkey',
        'ticker',
        'company_naics',
        # Time
        'year_month',
        # Partisan lean (core output)
        'brand_lean_2020',
        'brand_lean_2016',
        # Aggregation metadata
        'total_normalized_visits',
        'n_pois',
        'n_states',
        'n_cbsas',
        # Categories (mode across POIs)
        'top_category',
        'sub_category',
        'naics_code',
    ]

    return agg[output_cols]


def main():
    print("=" * 60)
    print("Task 1.5: Brand-Month Aggregation")
    print("=" * 60)

    # Load entity resolution lookup
    print("\nLoading entity resolution data...")
    brand_lookup = pq.read_table(ENTITY_RESOLUTION_PATH).to_pandas()
    print(f"  Loaded {len(brand_lookup):,} matched brands")

    # Keep columns needed for join and output
    brand_lookup = brand_lookup[[
        'safegraph_brand_id',
        'brand_name',
        'brand_n_locations',
        'brand_naics',
        'rcid',
        'company_name',
        'gvkey',
        'ticker',
        'company_naics',
    ]].copy()

    # Get list of input files
    input_files = sorted(INPUT_DIR.glob('partisan_lean_*.parquet'))
    print(f"\nFound {len(input_files)} monthly files to process")

    # Process each month
    all_results = []

    for i, file_path in enumerate(input_files, 1):
        year_month = file_path.stem.replace('partisan_lean_', '')
        print(f"\n[{i:2d}/{len(input_files)}] Processing {year_month}...", end=' ')

        # Load month data
        df = pq.read_table(file_path).to_pandas()
        n_input = len(df)

        # Aggregate
        result = aggregate_single_month(df, brand_lookup)

        if not result.empty:
            all_results.append(result)
            print(f"{n_input:,} POIs → {len(result):,} brands")
        else:
            print(f"{n_input:,} POIs → 0 brands (no matches)")

    # Combine all months
    print("\n" + "=" * 60)
    print("Combining results...")

    final_df = pd.concat(all_results, ignore_index=True)

    # Summary stats
    n_brand_months = len(final_df)
    n_unique_brands = final_df['brand_name'].nunique()
    n_months = final_df['year_month'].nunique()

    print(f"\nFinal dataset:")
    print(f"  {n_brand_months:,} brand-month observations")
    print(f"  {n_unique_brands:,} unique brands")
    print(f"  {n_months} months")

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / 'brand_month_partisan_lean.parquet'

    print(f"\nSaving to {output_path}...")
    final_df.to_parquet(output_path, index=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size_mb:.1f} MB")

    # Print sample
    print("\nSample output (first 5 rows):")
    print(final_df.head().to_string())

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
