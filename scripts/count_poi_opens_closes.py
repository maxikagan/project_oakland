#!/usr/bin/env python3
"""
Count POI openings and closures during the measurement period.
Uses vectorized operations for fast processing.
"""

import pandas as pd
import glob
import os

POI_DIR = "/global/scratch/users/maxkagan/01_foot_traffic_location/safegraph/poi_data_dewey_10_21_2024/"
OUTPUT_DIR = "/global/scratch/users/maxkagan/project_oakland/poi_lifecycle_analysis/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    poi_files = sorted(glob.glob(f"{POI_DIR}Global_Places_POI_Data-*.csv.gz"))
    print(f"Found {len(poi_files)} POI files")

    cols_to_read = [
        'PLACEKEY', 'LOCATION_NAME', 'BRANDS', 'TOP_CATEGORY', 'SUB_CATEGORY',
        'NAICS_CODE', 'REGION', 'CITY', 'OPENED_ON', 'CLOSED_ON', 'TRACKING_CLOSED_SINCE'
    ]

    dfs = []
    for i, f in enumerate(poi_files):
        print(f"Reading file {i+1}/{len(poi_files)}: {os.path.basename(f)}")
        df = pd.read_csv(f, compression='gzip', usecols=cols_to_read, dtype=str)
        dfs.append(df)

    print("Concatenating all files...")
    all_pois = pd.concat(dfs, ignore_index=True)
    print(f"Total POIs: {len(all_pois):,}")

    print("Parsing dates...")
    all_pois['opened_date'] = pd.to_datetime(all_pois['OPENED_ON'], errors='coerce')
    all_pois['closed_date'] = pd.to_datetime(all_pois['CLOSED_ON'], errors='coerce')
    all_pois['tracking_closed_date'] = pd.to_datetime(all_pois['TRACKING_CLOSED_SINCE'], errors='coerce')

    all_pois['closure_date'] = all_pois['closed_date'].fillna(all_pois['tracking_closed_date'])

    all_pois['opened_year'] = all_pois['opened_date'].dt.year
    all_pois['closed_year'] = all_pois['closure_date'].dt.year

    print("\n" + "="*60)
    print("POI LIFECYCLE SUMMARY")
    print("="*60)

    total = len(all_pois)
    with_opened = all_pois['opened_date'].notna().sum()
    with_closed = all_pois['closure_date'].notna().sum()

    print(f"Total POIs: {total:,}")
    print(f"POIs with opened_on date: {with_opened:,} ({100*with_opened/total:.1f}%)")
    print(f"POIs with closure date: {with_closed:,} ({100*with_closed/total:.1f}%)")

    opened_2019_2024 = all_pois[(all_pois['opened_year'] >= 2019) & (all_pois['opened_year'] <= 2024)]
    closed_2019_2024 = all_pois[(all_pois['closed_year'] >= 2019) & (all_pois['closed_year'] <= 2024)]

    print(f"\nOpenings during 2019-2024: {len(opened_2019_2024):,}")
    print(f"Closures during 2019-2024: {len(closed_2019_2024):,}")

    print("\nOpenings by year:")
    opened_by_year = all_pois[all_pois['opened_year'] >= 2015].groupby('opened_year').size()
    for year, count in opened_by_year.items():
        print(f"  {int(year)}: {count:,}")

    print("\nClosures by year:")
    closed_by_year = all_pois[all_pois['closed_year'] >= 2015].groupby('closed_year').size()
    for year, count in closed_by_year.items():
        print(f"  {int(year)}: {count:,}")

    print("\nTop 10 categories for openings (2019-2024):")
    top_opened = opened_2019_2024.groupby('TOP_CATEGORY').size().sort_values(ascending=False).head(10)
    for cat, count in top_opened.items():
        print(f"  {cat}: {count:,}")

    print("\nTop 10 categories for closures (2019-2024):")
    top_closed = closed_2019_2024.groupby('TOP_CATEGORY').size().sort_values(ascending=False).head(10)
    for cat, count in top_closed.items():
        print(f"  {cat}: {count:,}")

    print("\nSaving output files...")

    output_cols = ['PLACEKEY', 'LOCATION_NAME', 'BRANDS', 'TOP_CATEGORY', 'SUB_CATEGORY',
                   'NAICS_CODE', 'REGION', 'CITY', 'opened_date', 'closure_date']

    all_pois[output_cols].to_parquet(f"{OUTPUT_DIR}poi_lifecycle_all.parquet", index=False)
    print(f"Saved: poi_lifecycle_all.parquet ({len(all_pois):,} rows)")

    opened_2019_2024[output_cols].to_parquet(f"{OUTPUT_DIR}poi_opened_2019_2024.parquet", index=False)
    print(f"Saved: poi_opened_2019_2024.parquet ({len(opened_2019_2024):,} rows)")

    closed_2019_2024[output_cols].to_parquet(f"{OUTPUT_DIR}poi_closed_2019_2024.parquet", index=False)
    print(f"Saved: poi_closed_2019_2024.parquet ({len(closed_2019_2024):,} rows)")

    summary = {
        'total_pois': int(total),
        'with_opened_on': int(with_opened),
        'with_closed_on': int(with_closed),
        'opened_2019_2024': int(len(opened_2019_2024)),
        'closed_2019_2024': int(len(closed_2019_2024)),
        'opened_by_year': {int(k): int(v) for k, v in opened_by_year.items()},
        'closed_by_year': {int(k): int(v) for k, v in closed_by_year.items()},
    }

    import json
    with open(f"{OUTPUT_DIR}poi_lifecycle_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: poi_lifecycle_summary.json")

    print("\nDone!")

if __name__ == "__main__":
    main()
