#!/usr/bin/env python3
"""
Step 5: Combine all state outputs and partition by month.

This script:
1. Reads all state-level partisan lean files
2. Combines into single national dataset
3. Repartitions by month (YYYY-MM)
4. Saves as individual month parquet files

Output: /global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean/national_full/
Files: 2019-01.parquet through 2025-07.parquet
"""

import logging
import pandas as pd
from pathlib import Path
import glob

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/intermediate/advan_partisan")
OUTPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean/national_full")


def get_unique_months(state_files):
    """Scan all state files to find all unique months without loading full data."""
    logger.info("Scanning files to identify all months...")
    all_months = set()

    for file_path in state_files:
        try:
            df = pd.read_parquet(file_path, columns=['date_range_start'])
            df['date_range_start'] = pd.to_datetime(df['date_range_start'])
            months = df['date_range_start'].dt.strftime('%Y-%m').unique()
            all_months.update(months)
        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")
            return None

    return sorted(all_months)


def combine_and_partition():
    """Combine all state files and partition by month (memory-efficient)."""
    logger.info("Starting Step 5: Combine and partition by month...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    state_files = sorted(glob.glob(str(INPUT_DIR / "*.parquet")))
    logger.info(f"Found {len(state_files)} state files")

    if not state_files:
        logger.error(f"No parquet files found in {INPUT_DIR}")
        return False

    unique_months = get_unique_months(state_files)
    if unique_months is None:
        return False

    logger.info(f"Found {len(unique_months)} unique months: {unique_months[0]} to {unique_months[-1]}")

    total_rows = 0
    stats_accum = {
        'rep_lean_2020_sum': 0.0,
        'rep_lean_2016_sum': 0.0,
        'count': 0
    }

    for month in unique_months:
        logger.info(f"Processing month {month}...")
        month_data_chunks = []

        for file_path in state_files:
            try:
                df = pd.read_parquet(file_path)
                df['date_range_start'] = pd.to_datetime(df['date_range_start'])
                df['year_month'] = df['date_range_start'].dt.strftime('%Y-%m')

                month_chunk = df[df['year_month'] == month].copy()
                if len(month_chunk) > 0:
                    month_chunk = month_chunk.drop(columns=['year_month'])
                    month_data_chunks.append(month_chunk)

            except Exception as e:
                logger.error(f"Failed to process {file_path} for month {month}: {e}")
                return False

        if not month_data_chunks:
            logger.warning(f"  {month}: No data found")
            continue

        month_df = pd.concat(month_data_chunks, ignore_index=True)
        total_rows += len(month_df)

        stats_accum['rep_lean_2020_sum'] += month_df['rep_lean_2020'].sum()
        stats_accum['rep_lean_2016_sum'] += month_df['rep_lean_2016'].sum()
        stats_accum['count'] += len(month_df)

        try:
            output_file = OUTPUT_DIR / f"{month}.parquet"
            month_df.to_parquet(output_file, index=False, compression='snappy')
            logger.info(f"  {month}: {len(month_df):,} rows saved")
        except Exception as e:
            logger.error(f"Failed to save month {month}: {e}")
            return False

        del month_df, month_data_chunks

    logger.info("Summary statistics:")
    logger.info(f"  Total POI-month observations: {total_rows:,}")
    if stats_accum['count'] > 0:
        logger.info(f"  Mean rep_lean_2020: {stats_accum['rep_lean_2020_sum'] / stats_accum['count']:.4f}")
        logger.info(f"  Mean rep_lean_2016: {stats_accum['rep_lean_2016_sum'] / stats_accum['count']:.4f}")

    logger.info(f"Step 5 complete: {len(unique_months)} monthly files created in {OUTPUT_DIR}")
    return True


def main():
    """Run Step 5."""
    try:
        success = combine_and_partition()

        if success:
            logger.info("Step 5 completed successfully!")
            return 0
        else:
            logger.error("Step 5 failed")
            return 1

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
