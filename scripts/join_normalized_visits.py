#!/usr/bin/env python3
"""
Join extracted NORMALIZED_VISITS_BY_STATE_SCALING to existing partisan lean data.

Run AFTER extract_normalized_visits.py array job completes.

Usage:
    python3 join_normalized_visits.py
"""

import logging
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
NORMALIZED_DIR = PROJECT_DIR / "intermediate" / "normalized_visits_by_file"
PARTISAN_DIR = PROJECT_DIR / "outputs" / "national"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "national_with_normalized"


def load_all_normalized_visits():
    """Load and combine all normalized visits parquet files."""
    logger.info("Loading normalized visits files...")

    files = list(NORMALIZED_DIR.glob("*.parquet"))
    logger.info(f"Found {len(files)} normalized visits files")

    if len(files) == 0:
        raise FileNotFoundError(f"No parquet files found in {NORMALIZED_DIR}")

    dfs = []
    for i, f in enumerate(files):
        if i % 200 == 0:
            logger.info(f"Loading file {i+1}/{len(files)}...")
        dfs.append(pd.read_parquet(f))

    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined: {len(combined):,} total rows")

    combined['date_range_start'] = pd.to_datetime(combined['date_range_start'])

    return combined


def process_month(month_file: Path, normalized_df: pd.DataFrame):
    """Join normalized visits to one month's partisan lean data."""
    logger.info(f"Processing {month_file.name}...")

    partisan_df = pd.read_parquet(month_file)
    partisan_df['date_range_start'] = pd.to_datetime(partisan_df['date_range_start'])

    merged = partisan_df.merge(
        normalized_df[['placekey', 'date_range_start', 'normalized_visits_by_state_scaling']],
        on=['placekey', 'date_range_start'],
        how='left'
    )

    match_rate = merged['normalized_visits_by_state_scaling'].notna().mean() * 100
    logger.info(f"  {month_file.name}: {len(merged):,} rows, {match_rate:.1f}% matched")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / month_file.name
    merged.to_parquet(output_path, index=False, compression='snappy')

    return month_file.name, len(merged), match_rate


def main():
    logger.info("=== Joining Normalized Visits to Partisan Lean Data ===")

    normalized_df = load_all_normalized_visits()

    month_files = sorted(PARTISAN_DIR.glob("partisan_lean_*.parquet"))
    logger.info(f"Found {len(month_files)} monthly partisan lean files")

    results = []
    for month_file in month_files:
        result = process_month(month_file, normalized_df)
        results.append(result)

    logger.info("\n=== Summary ===")
    total_rows = sum(r[1] for r in results)
    avg_match = sum(r[2] for r in results) / len(results)
    logger.info(f"Total rows: {total_rows:,}")
    logger.info(f"Average match rate: {avg_match:.1f}%")
    logger.info(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
