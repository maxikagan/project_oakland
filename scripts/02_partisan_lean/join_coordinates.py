#!/usr/bin/env python3
"""
Join extracted coordinates to partisan lean data.

Reads:
  - outputs/poi_coordinates.parquet (placekey → lat, lon)
  - outputs/national_with_normalized/*.parquet (79 monthly files)

Outputs:
  - outputs/national_with_coords/*.parquet (79 monthly files with lat/lon added)

Usage:
    python3 join_coordinates.py
"""

import pandas as pd
from pathlib import Path
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
COORDS_PATH = PROJECT_DIR / "outputs" / "poi_coordinates.parquet"
INPUT_DIR = PROJECT_DIR / "outputs" / "national_with_normalized"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "national_with_coords"


def main():
    logger.info("=" * 60)
    logger.info("Joining coordinates to partisan lean data")
    logger.info("=" * 60)

    if not COORDS_PATH.exists():
        logger.error(f"Coordinates file not found: {COORDS_PATH}")
        logger.error("Run extract_coordinates.py first")
        return 1

    logger.info("Loading coordinates lookup...")
    coords_df = pd.read_parquet(COORDS_PATH)
    logger.info(f"Loaded {len(coords_df):,} POI coordinates")

    monthly_files = sorted(INPUT_DIR.glob("partisan_lean_*.parquet"))
    logger.info(f"Found {len(monthly_files)} monthly files to process")

    if not monthly_files:
        logger.error(f"No monthly files found in {INPUT_DIR}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    total_matched = 0

    for i, f in enumerate(monthly_files):
        logger.info(f"[{i+1}/{len(monthly_files)}] Processing {f.name}...")

        df = pd.read_parquet(f)
        initial_rows = len(df)

        merged = df.merge(
            coords_df,
            on='placekey',
            how='left'
        )

        matched = merged['latitude'].notna().sum()
        match_rate = (matched / len(merged)) * 100

        logger.info(f"  {initial_rows:,} rows, {match_rate:.1f}% matched with coordinates")

        output_path = OUTPUT_DIR / f.name
        merged.to_parquet(output_path, index=False, compression='snappy')

        total_rows += initial_rows
        total_matched += matched

    overall_match_rate = (total_matched / total_rows) * 100
    logger.info("=" * 60)
    logger.info(f"Complete! {len(monthly_files)} files processed")
    logger.info(f"Total rows: {total_rows:,}")
    logger.info(f"Overall coordinate match rate: {overall_match_rate:.1f}%")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
