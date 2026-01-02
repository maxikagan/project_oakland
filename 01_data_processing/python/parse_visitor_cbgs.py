"""
Parse visitor_home_cbgs and calculate weighted partisan lean per location.

For each POI, parses the visitor_home_cbgs JSON field, joins with CBG
partisan lean lookup, and computes weighted average Republican share.

Usage:
    python parse_visitor_cbgs.py --state OH --output /path/to/output.parquet
"""

import argparse
import pandas as pd
import json
from pathlib import Path
import numpy as np


def parse_visitor_cbgs(cbg_json: str) -> dict:
    """Parse visitor_home_cbgs JSON string to dict."""
    if pd.isna(cbg_json) or cbg_json == '' or cbg_json == '{}':
        return {}
    try:
        return json.loads(cbg_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def process_month(advan_file: Path, cbg_lookup: pd.DataFrame, month: str) -> pd.DataFrame:
    """
    Process one month of Advan data.

    Args:
        advan_file: Path to filtered Advan parquet file
        cbg_lookup: DataFrame with CBG partisan lean data
        month: Month string (e.g., "2023-01-01")

    Returns:
        DataFrame with placekey, month, rep_lean, total_visitors, etc.
    """
    print(f"  Processing: {advan_file.name}")

    # Read Advan data
    df = pd.read_parquet(advan_file)
    print(f"    Loaded {len(df):,} POIs")

    # Key columns we need
    keep_cols = ['placekey', 'location_name', 'brands', 'top_category',
                 'sub_category', 'naics_code', 'region', 'city',
                 'visitor_home_cbgs', 'visitor_daytime_cbgs']

    # Filter to available columns
    available_cols = [c for c in keep_cols if c in df.columns]
    df = df[available_cols].copy()

    # Parse visitor_home_cbgs and explode
    results = []

    for idx, row in df.iterrows():
        placekey = row['placekey']
        cbg_dict = parse_visitor_cbgs(row.get('visitor_home_cbgs', '{}'))

        if not cbg_dict:
            continue

        # Get metadata
        metadata = {col: row.get(col) for col in available_cols if col not in ['visitor_home_cbgs', 'visitor_daytime_cbgs']}

        # Sum up weighted partisan lean
        total_visitors = 0
        weighted_rep_sum = 0
        cbg_count = 0

        for cbg_id, visitor_count in cbg_dict.items():
            # Ensure cbg_id is 12 digits
            cbg_id_padded = str(cbg_id).zfill(12)

            # Look up partisan lean
            cbg_data = cbg_lookup[cbg_lookup['cbg_geoid'] == cbg_id_padded]

            if len(cbg_data) > 0:
                rep_share = cbg_data['two_party_rep_share_2020'].values[0]
                weighted_rep_sum += visitor_count * rep_share
                total_visitors += visitor_count
                cbg_count += 1

        if total_visitors > 0:
            rep_lean = weighted_rep_sum / total_visitors

            results.append({
                **metadata,
                'month': month,
                'rep_lean': rep_lean,
                'total_visitors': total_visitors,
                'cbg_count': cbg_count
            })

    result_df = pd.DataFrame(results)
    print(f"    Output: {len(result_df):,} POIs with valid visitor data")
    return result_df


def process_month_vectorized(advan_file: Path, cbg_lookup: pd.DataFrame, month: str) -> pd.DataFrame:
    """
    Process one month of Advan data (vectorized version - faster).
    """
    print(f"  Processing: {advan_file.name}")

    # Read Advan data
    df = pd.read_parquet(advan_file)
    print(f"    Loaded {len(df):,} POIs")

    # Validate required columns exist (UPPERCASE in Advan files)
    required_cols = ['PLACEKEY', 'VISITOR_HOME_CBGS']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}. Available: {list(df.columns)[:10]}...")

    # Parse all VISITOR_HOME_CBGS
    df['parsed_cbgs'] = df['VISITOR_HOME_CBGS'].apply(parse_visitor_cbgs)

    # Filter to rows with visitor data
    df = df[df['parsed_cbgs'].apply(len) > 0].copy()
    print(f"    POIs with visitor data: {len(df):,}")

    if len(df) == 0:
        return pd.DataFrame()

    # Explode to long format
    exploded = df.explode('parsed_cbgs')
    # parsed_cbgs is now a dict, need to convert to cbg_id, count
    # Actually, explode on dict doesn't work that way. Let me fix this.

    # Better approach: create list of (cbg_id, count) tuples first
    def cbg_dict_to_list(d):
        return [(str(k).zfill(12), v) for k, v in d.items()]

    df['cbg_list'] = df['parsed_cbgs'].apply(cbg_dict_to_list)

    # Now explode
    df = df.explode('cbg_list')
    df = df[df['cbg_list'].notna()].copy()

    if len(df) == 0:
        return pd.DataFrame()

    # Extract cbg_id and visitor_count
    df['cbg_geoid'] = df['cbg_list'].apply(lambda x: x[0])
    df['visitor_count'] = df['cbg_list'].apply(lambda x: x[1])

    # Join with CBG lookup
    df = df.merge(cbg_lookup[['cbg_geoid', 'two_party_rep_share_2020']],
                  on='cbg_geoid', how='left')

    # Filter to matched CBGs
    matched = df[df['two_party_rep_share_2020'].notna()].copy()
    print(f"    Matched CBG records: {len(matched):,}")

    if len(matched) == 0:
        return pd.DataFrame()

    # Calculate weighted sum
    matched['weighted_rep'] = matched['visitor_count'] * matched['two_party_rep_share_2020']

    # Aggregate by PLACEKEY (UPPERCASE in Advan files)
    keep_cols = ['PLACEKEY', 'LOCATION_NAME', 'BRANDS', 'TOP_CATEGORY',
                 'SUB_CATEGORY', 'NAICS_CODE', 'REGION', 'CITY']
    available_cols = [c for c in keep_cols if c in matched.columns]

    agg_dict = {
        'visitor_count': 'sum',
        'weighted_rep': 'sum',
        'cbg_geoid': 'nunique'  # count unique CBGs
    }

    # Add first value for metadata columns
    for col in available_cols:
        if col != 'PLACEKEY':
            agg_dict[col] = 'first'

    grouped = matched.groupby('PLACEKEY').agg(agg_dict).reset_index()

    # Rename to lowercase for output consistency
    grouped = grouped.rename(columns={
        'PLACEKEY': 'placekey',
        'LOCATION_NAME': 'location_name',
        'BRANDS': 'brands',
        'TOP_CATEGORY': 'top_category',
        'SUB_CATEGORY': 'sub_category',
        'NAICS_CODE': 'naics_code',
        'REGION': 'region',
        'CITY': 'city',
        'visitor_count': 'total_visitors',
        'cbg_geoid': 'cbg_count'
    })

    # Calculate final rep_lean
    grouped['rep_lean'] = grouped['weighted_rep'] / grouped['total_visitors']
    grouped['month'] = month

    # Clean up
    grouped = grouped.drop(columns=['weighted_rep'])

    print(f"    Final output: {len(grouped):,} POIs")
    return grouped


def main():
    parser = argparse.ArgumentParser(description="Parse visitor CBGs and calculate partisan lean")
    parser.add_argument("--state", default="OH", help="State abbreviation (default: OH)")
    parser.add_argument("--input-dir",
                        default="/global/scratch/users/maxkagan/project_oakland/intermediate/advan_2023_filtered",
                        help="Directory with filtered Advan parquet files")
    parser.add_argument("--cbg-lookup",
                        default="/global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_ohio.parquet",
                        help="CBG partisan lean lookup file")
    parser.add_argument("--output",
                        default="/global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean/ohio_2023.parquet",
                        help="Output parquet file")

    args = parser.parse_args()

    # Load CBG lookup
    print(f"Loading CBG lookup from: {args.cbg_lookup}")
    cbg_lookup = pd.read_parquet(args.cbg_lookup)
    print(f"  {len(cbg_lookup):,} CBGs loaded")

    # Validate CBG lookup
    if len(cbg_lookup) == 0:
        raise ValueError(f"CBG lookup file is empty: {args.cbg_lookup}")
    required_lookup_cols = ['cbg_geoid', 'two_party_rep_share_2020']
    missing = [c for c in required_lookup_cols if c not in cbg_lookup.columns]
    if missing:
        raise ValueError(f"CBG lookup missing columns: {missing}. Available: {list(cbg_lookup.columns)}")

    # Find all monthly files (in parquet/ subdirectory)
    input_dir = Path(args.input_dir) / "parquet"
    monthly_files = sorted(input_dir.glob(f"{args.state}_*.parquet"))
    print(f"Found {len(monthly_files)} monthly files")

    if len(monthly_files) == 0:
        print("No input files found!")
        return

    # Process each month
    all_results = []
    for f in monthly_files:
        # Extract month from filename (e.g., "OH_2023-01-01.parquet")
        month = f.stem.split('_')[1]
        result = process_month_vectorized(f, cbg_lookup, month)
        if len(result) > 0:
            all_results.append(result)

    # Combine all months
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        print(f"\nTotal: {len(combined):,} POI-month observations")

        # Save
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_parquet(output_path, index=False)
        print(f"Saved to: {output_path}")

        # Print summary
        print(f"\nSummary:")
        print(f"  Unique POIs: {combined['placekey'].nunique():,}")
        print(f"  Months covered: {combined['month'].nunique()}")
        print(f"  Mean rep_lean: {combined['rep_lean'].mean():.3f}")
        print(f"  Std dev: {combined['rep_lean'].std():.3f}")
    else:
        print("No results to save!")


if __name__ == "__main__":
    main()
