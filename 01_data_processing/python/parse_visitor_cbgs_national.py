"""
Parse visitor_home_cbgs and calculate weighted partisan lean per location.

National version: processes all filtered state files for a given state,
using the national CBG lookup.

Usage:
    python parse_visitor_cbgs_national.py --state OH
    python parse_visitor_cbgs_national.py --state CA --year 2023
"""

import argparse
import pandas as pd
import json
from pathlib import Path
import numpy as np
import sys


def parse_visitor_cbgs(cbg_json: str) -> dict:
    """Parse visitor_home_cbgs JSON string to dict."""
    if pd.isna(cbg_json) or cbg_json == '' or cbg_json == '{}':
        return {}
    try:
        return json.loads(cbg_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def process_month_vectorized(advan_file: Path, cbg_lookup: pd.DataFrame, month: str) -> pd.DataFrame:
    """
    Process one month of filtered Advan data using vectorized operations.
    """
    print(f"  Processing: {advan_file.name}")

    df = pd.read_parquet(advan_file)
    print(f"    Loaded {len(df):,} POIs")

    required_cols = ['PLACEKEY', 'VISITOR_HOME_CBGS']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}. Available: {list(df.columns)[:10]}...")

    df['parsed_cbgs'] = df['VISITOR_HOME_CBGS'].apply(parse_visitor_cbgs)
    df = df[df['parsed_cbgs'].apply(len) > 0].copy()
    print(f"    POIs with visitor data: {len(df):,}")

    if len(df) == 0:
        return pd.DataFrame()

    def cbg_dict_to_list(d):
        return [(str(k).zfill(12), v) for k, v in d.items()]

    df['cbg_list'] = df['parsed_cbgs'].apply(cbg_dict_to_list)
    df = df.explode('cbg_list')
    df = df[df['cbg_list'].notna()].copy()

    if len(df) == 0:
        return pd.DataFrame()

    df['cbg_geoid'] = df['cbg_list'].apply(lambda x: x[0])
    df['visitor_count'] = df['cbg_list'].apply(lambda x: x[1])

    df = df.merge(cbg_lookup[['cbg_geoid', 'two_party_rep_share_2020']],
                  on='cbg_geoid', how='left')

    matched = df[df['two_party_rep_share_2020'].notna()].copy()
    print(f"    Matched CBG records: {len(matched):,}")

    if len(matched) == 0:
        return pd.DataFrame()

    matched['weighted_rep'] = matched['visitor_count'] * matched['two_party_rep_share_2020']

    keep_cols = ['PLACEKEY', 'LOCATION_NAME', 'BRANDS', 'TOP_CATEGORY',
                 'SUB_CATEGORY', 'NAICS_CODE', 'REGION', 'CITY', 'POSTAL_CODE',
                 'LATITUDE', 'LONGITUDE', 'RAW_VISIT_COUNTS', 'RAW_VISITOR_COUNTS']
    available_cols = [c for c in keep_cols if c in matched.columns]

    agg_dict = {
        'visitor_count': 'sum',
        'weighted_rep': 'sum',
        'cbg_geoid': 'nunique'
    }

    for col in available_cols:
        if col != 'PLACEKEY':
            agg_dict[col] = 'first'

    grouped = matched.groupby('PLACEKEY').agg(agg_dict).reset_index()

    grouped = grouped.rename(columns={
        'PLACEKEY': 'placekey',
        'LOCATION_NAME': 'location_name',
        'BRANDS': 'brands',
        'TOP_CATEGORY': 'top_category',
        'SUB_CATEGORY': 'sub_category',
        'NAICS_CODE': 'naics_code',
        'REGION': 'region',
        'CITY': 'city',
        'POSTAL_CODE': 'postal_code',
        'LATITUDE': 'latitude',
        'LONGITUDE': 'longitude',
        'RAW_VISIT_COUNTS': 'raw_visit_counts',
        'RAW_VISITOR_COUNTS': 'raw_visitor_counts',
        'visitor_count': 'total_visitors',
        'cbg_geoid': 'cbg_count'
    })

    grouped['rep_lean'] = grouped['weighted_rep'] / grouped['total_visitors']
    grouped['month'] = month
    grouped = grouped.drop(columns=['weighted_rep'])

    print(f"    Final output: {len(grouped):,} POIs")
    return grouped


def main():
    parser = argparse.ArgumentParser(description="Parse visitor CBGs and calculate partisan lean (national)")
    parser.add_argument("--state", required=True, help="State abbreviation (e.g., OH, CA)")
    parser.add_argument("--year", type=int, help="Optional: limit to specific year")
    parser.add_argument("--input-dir",
                        default="/global/scratch/users/maxkagan/project_oakland/intermediate/advan_national_filtered/parquet",
                        help="Directory with filtered Advan parquet files")
    parser.add_argument("--cbg-lookup",
                        default="/global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national.parquet",
                        help="National CBG partisan lean lookup file")
    parser.add_argument("--output-dir",
                        default="/global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean",
                        help="Output directory")

    args = parser.parse_args()
    state = args.state.upper()

    print(f"Loading CBG lookup from: {args.cbg_lookup}")
    cbg_lookup = pd.read_parquet(args.cbg_lookup)
    print(f"  {len(cbg_lookup):,} CBGs loaded")

    if len(cbg_lookup) == 0:
        print("ERROR: CBG lookup file is empty", file=sys.stderr)
        sys.exit(1)

    required_lookup_cols = ['cbg_geoid', 'two_party_rep_share_2020']
    missing = [c for c in required_lookup_cols if c not in cbg_lookup.columns]
    if missing:
        print(f"ERROR: CBG lookup missing columns: {missing}", file=sys.stderr)
        sys.exit(1)

    input_dir = Path(args.input_dir)
    pattern = f"{state}_*.parquet"
    if args.year:
        pattern = f"{state}_{args.year}-*.parquet"

    monthly_files = sorted(input_dir.glob(pattern))
    print(f"Found {len(monthly_files)} monthly files for {state}")

    if len(monthly_files) == 0:
        print(f"ERROR: No input files found matching {pattern} in {input_dir}", file=sys.stderr)
        sys.exit(1)

    all_results = []
    for f in monthly_files:
        month = f.stem.split('_')[1]
        result = process_month_vectorized(f, cbg_lookup, month)
        if len(result) > 0:
            all_results.append(result)

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        print(f"\nTotal: {len(combined):,} POI-month observations")

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.year:
            output_file = output_dir / f"{state}_{args.year}.parquet"
        else:
            output_file = output_dir / f"{state}_all_years.parquet"

        combined.to_parquet(output_file, index=False)
        print(f"Saved to: {output_file}")

        print(f"\nSummary for {state}:")
        print(f"  Unique POIs: {combined['placekey'].nunique():,}")
        print(f"  Months covered: {combined['month'].nunique()}")
        print(f"  Mean rep_lean: {combined['rep_lean'].mean():.3f}")
        print(f"  Std dev: {combined['rep_lean'].std():.3f}")
        print(f"  Min: {combined['rep_lean'].min():.3f}")
        print(f"  Max: {combined['rep_lean'].max():.3f}")
    else:
        print("ERROR: No results to save!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
