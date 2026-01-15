#!/usr/bin/env python3
"""
Step 3: Filter Advan foot traffic data by state, add CBSA, select columns.

This is an array job script. It:
1. Reads csv.gz files from new complete download (Jan 2019 - Jul 2025)
2. Filters by REGION (state)
3. Adds CBSA (Metropolitan Statistical Area) via POI_CBG lookup
4. Selects relevant columns
5. Saves filtered data by state for Step 4 processing

Usage:
  python3 03_filter_advan_by_state.py <STATE>

Example:
  python3 03_filter_advan_by_state.py CA

Output: /global/scratch/users/maxkagan/project_oakland/intermediate/advan_filtered/{STATE}/advan_{STATE}_filtered.parquet
"""

import sys
import logging
import pandas as pd
from pathlib import Path
import glob
import os
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ADVAN_DATA_DIR = Path("/global/scratch/users/maxkagan/project_oakland/foot_traffic_monthly_complete_2026-01-12/monthly-patterns-foot-traffic")
CBSA_CROSSWALK_PATH = Path("/global/scratch/users/maxkagan/project_oakland/inputs/cbsa_crosswalk.parquet")
OUTPUT_BASE_DIR = Path("/global/scratch/users/maxkagan/project_oakland/intermediate/advan_filtered")

COLUMNS_TO_SELECT = [
    'PLACEKEY',
    'DATE_RANGE_START',
    'BRANDS',
    'TOP_CATEGORY',
    'SUB_CATEGORY',
    'NAICS_CODE',
    'CITY',
    'REGION',
    'POI_CBG',
    'PARENT_PLACEKEY',
    'MEDIAN_DWELL',
    'VISITOR_HOME_CBGS',
    'RAW_VISITOR_COUNTS'
]

COLUMN_RENAME = {
    'PLACEKEY': 'placekey',
    'DATE_RANGE_START': 'date_range_start',
    'BRANDS': 'brand',
    'TOP_CATEGORY': 'top_category',
    'SUB_CATEGORY': 'sub_category',
    'NAICS_CODE': 'naics_code',
    'CITY': 'city',
    'REGION': 'region',
    'POI_CBG': 'poi_cbg',
    'PARENT_PLACEKEY': 'parent_placekey',
    'MEDIAN_DWELL': 'median_dwell',
    'VISITOR_HOME_CBGS': 'visitor_home_cbgs',
    'RAW_VISITOR_COUNTS': 'raw_visitor_counts'
}


def load_cbsa_crosswalk():
    """Load CBSA crosswalk for county → MSA mapping."""
    if not CBSA_CROSSWALK_PATH.exists():
        logger.warning(f"CBSA crosswalk not found at {CBSA_CROSSWALK_PATH}")
        return None

    try:
        cbsa_df = pd.read_parquet(CBSA_CROSSWALK_PATH)
        cbsa_lookup = dict(zip(cbsa_df['county_fips_full'], cbsa_df['cbsa_title']))
        logger.info(f"Loaded CBSA crosswalk with {len(cbsa_lookup)} counties")
        return cbsa_lookup
    except Exception as e:
        logger.warning(f"Failed to load CBSA crosswalk: {e}")
        return None


def process_single_file(args):
    """Process a single csv.gz file and filter by state."""
    file_path, state, columns = args

    try:
        df = pd.read_csv(
            file_path,
            compression='gzip',
            usecols=lambda c: c in columns,
            dtype={'POI_CBG': str, 'PLACEKEY': str, 'NAICS_CODE': str}
        )

        df_state = df[df['REGION'] == state]

        if len(df_state) == 0:
            return None

        return df_state

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None


def process_state(state, cbsa_lookup):
    """Filter Advan data for a single state."""
    logger.info(f"Processing state: {state}")

    output_dir = OUTPUT_BASE_DIR / state
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(glob.glob(str(ADVAN_DATA_DIR / "*.csv.gz")))
    logger.info(f"Found {len(csv_files)} csv.gz files")

    if not csv_files:
        logger.error(f"No csv.gz files found in {ADVAN_DATA_DIR}")
        return False

    state_data = []
    processed_files = 0
    files_with_data = 0

    n_workers = min(8, int(os.environ.get('SLURM_CPUS_PER_TASK', multiprocessing.cpu_count())))
    logger.info(f"Using {n_workers} workers for parallel processing")

    logger.info("Validating columns in first file...")
    sample_df = pd.read_csv(csv_files[0], compression='gzip', nrows=5)
    missing_cols = [c for c in COLUMNS_TO_SELECT if c not in sample_df.columns]
    if missing_cols:
        logger.error(f"Missing columns: {missing_cols}")
        logger.info(f"Available columns: {sample_df.columns.tolist()}")
        return False
    logger.info("All required columns found")

    args_list = [(f, state, COLUMNS_TO_SELECT) for f in csv_files]

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(process_single_file, args_list))

    for result in results:
        processed_files += 1
        if result is not None and len(result) > 0:
            state_data.append(result)
            files_with_data += 1

        if processed_files % 200 == 0:
            logger.info(f"  Processed {processed_files}/{len(csv_files)} files, {files_with_data} with data")

    logger.info(f"{state}: Processed {processed_files} files, {files_with_data} contained data")

    if not state_data:
        logger.warning(f"{state}: No data found for this state")
        return True

    logger.info(f"{state}: Combining {len(state_data)} file chunks...")
    combined_df = pd.concat(state_data, ignore_index=True)

    combined_df = combined_df.rename(columns=COLUMN_RENAME)

    if cbsa_lookup is not None:
        logger.info(f"{state}: Adding CBSA titles...")
        combined_df['poi_cbg'] = combined_df['poi_cbg'].fillna('').astype(str).str.zfill(12)
        combined_df['county_fips'] = combined_df['poi_cbg'].str[:5]
        combined_df['cbsa_title'] = combined_df['county_fips'].map(cbsa_lookup)
        combined_df = combined_df.drop(columns=['county_fips'])
        cbsa_coverage = combined_df['cbsa_title'].notna().mean() * 100
        logger.info(f"{state}: CBSA coverage: {cbsa_coverage:.1f}%")
    else:
        combined_df['cbsa_title'] = None

    logger.info(f"{state}: {len(combined_df)} rows total")

    try:
        output_file = output_dir / f"advan_{state}_filtered.parquet"
        combined_df.to_parquet(output_file, index=False, compression='snappy')
        logger.info(f"{state}: Saved to {output_file}")

        logger.info(f"{state}: Date range: {combined_df['date_range_start'].min()} to {combined_df['date_range_start'].max()}")
        logger.info(f"{state}: Unique POIs: {combined_df['placekey'].nunique()}")

        return True
    except Exception as e:
        logger.error(f"{state}: Failed to save output: {e}")
        return False


def main():
    """Run Step 3 for specified state."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <STATE>")
        print(f"Example: {sys.argv[0]} CA")
        sys.exit(1)

    state = sys.argv[1].upper()

    if not state.isalpha() or len(state) != 2:
        logger.error(f"Invalid state code: {state}")
        sys.exit(1)

    cbsa_lookup = load_cbsa_crosswalk()

    success = process_state(state, cbsa_lookup)

    if success:
        logger.info(f"Step 3 complete for {state}")
        sys.exit(0)
    else:
        logger.error(f"Step 3 failed for {state}")
        sys.exit(1)


if __name__ == "__main__":
    main()
