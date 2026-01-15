#!/usr/bin/env python3
"""
Efficient single-pass partisan lean computation.

Processes ONE csv.gz file directly, computing partisan lean for all POIs.
Designed for SLURM array jobs (2,096 tasks, one per file).

Usage:
    python3 compute_partisan_lean_direct.py <file_index>

    file_index: 1-based line number in file_list.txt
"""

import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path("/global/scratch/users/maxkagan/project_oakland")
FILE_LIST_PATH = PROJECT_DIR / "inputs" / "advan_file_list.txt"
CBG_LOOKUP_PATH = PROJECT_DIR / "inputs" / "cbg_partisan_lean_national_both_years.parquet"
CBSA_CROSSWALK_PATH = PROJECT_DIR / "inputs" / "cbsa_crosswalk.parquet"
OUTPUT_DIR = PROJECT_DIR / "intermediate" / "partisan_lean_by_file"

COLUMNS_TO_READ = [
    'PLACEKEY', 'DATE_RANGE_START', 'BRANDS',
    'TOP_CATEGORY', 'SUB_CATEGORY', 'NAICS_CODE',
    'CITY', 'REGION', 'POI_CBG', 'PARENT_PLACEKEY',
    'MEDIAN_DWELL', 'VISITOR_HOME_CBGS', 'RAW_VISITOR_COUNTS'
]

CBG_DICT_2020 = {}
CBG_DICT_2016 = {}
CBSA_LOOKUP = {}


def load_lookups():
    """Load CBG partisan lean and CBSA lookups into global dicts."""
    global CBG_DICT_2020, CBG_DICT_2016, CBSA_LOOKUP

    logger.info("Loading CBG lookup...")
    cbg_df = pd.read_parquet(CBG_LOOKUP_PATH)
    CBG_DICT_2020 = dict(zip(cbg_df['GEOID'], cbg_df['two_party_rep_share_2020']))
    CBG_DICT_2016 = dict(zip(cbg_df['GEOID'], cbg_df['two_party_rep_share_2016']))
    logger.info(f"Loaded {len(CBG_DICT_2020):,} CBGs")

    if CBSA_CROSSWALK_PATH.exists():
        logger.info("Loading CBSA crosswalk...")
        cbsa_df = pd.read_parquet(CBSA_CROSSWALK_PATH)
        CBSA_LOOKUP = dict(zip(cbsa_df['county_fips_full'], cbsa_df['cbsa_title']))
        logger.info(f"Loaded {len(CBSA_LOOKUP):,} county→CBSA mappings")


def parse_visitor_cbgs(visitor_cbgs_json):
    """Parse VISITOR_HOME_CBGS JSON to dict. Handles double-encoded JSON."""
    if pd.isna(visitor_cbgs_json) or visitor_cbgs_json is None:
        return {}
    if isinstance(visitor_cbgs_json, dict):
        return visitor_cbgs_json
    try:
        parsed = json.loads(visitor_cbgs_json)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def compute_partisan_lean(visitor_cbgs_json):
    """
    Compute weighted partisan lean from visitor CBGs.

    Returns: (rep_lean_2020, rep_lean_2016, total_visitors, matched_visitors)
    """
    visitor_cbgs = parse_visitor_cbgs(visitor_cbgs_json)

    if not visitor_cbgs:
        return np.nan, np.nan, 0, 0

    total_visitors = 0
    matched_visitors = 0
    weighted_2020 = 0.0
    weighted_2016 = 0.0

    for cbg_geoid, count in visitor_cbgs.items():
        try:
            count = int(count)
        except (ValueError, TypeError):
            continue

        cbg_str = str(cbg_geoid).zfill(12)
        total_visitors += count

        if cbg_str in CBG_DICT_2020:
            rep_2020 = CBG_DICT_2020[cbg_str]
            rep_2016 = CBG_DICT_2016.get(cbg_str, 0.5)
            weighted_2020 += rep_2020 * count
            weighted_2016 += rep_2016 * count
            matched_visitors += count

    if matched_visitors == 0:
        return np.nan, np.nan, total_visitors, 0

    return (
        weighted_2020 / matched_visitors,
        weighted_2016 / matched_visitors,
        total_visitors,
        matched_visitors
    )


def process_file(file_path: Path):
    """Process a single csv.gz file and compute partisan lean for all POIs."""
    logger.info(f"Reading {file_path.name}...")

    df = pd.read_csv(
        file_path,
        compression='gzip',
        usecols=lambda c: c in COLUMNS_TO_READ,
        dtype={'POI_CBG': str, 'PLACEKEY': str, 'NAICS_CODE': str}
    )
    logger.info(f"Read {len(df):,} rows")

    if len(df) == 0:
        return None

    df.columns = df.columns.str.lower()
    df = df.rename(columns={'brands': 'brand'})

    if CBSA_LOOKUP:
        df['poi_cbg'] = df['poi_cbg'].fillna('').astype(str).str.zfill(12)
        df['county_fips'] = df['poi_cbg'].str[:5]
        df['cbsa_title'] = df['county_fips'].map(CBSA_LOOKUP)
        df = df.drop(columns=['county_fips'])
    else:
        df['cbsa_title'] = None

    logger.info("Computing partisan lean...")
    results = df['visitor_home_cbgs'].apply(compute_partisan_lean)

    df['rep_lean_2020'] = results.apply(lambda x: x[0])
    df['rep_lean_2016'] = results.apply(lambda x: x[1])
    df['total_visitors'] = results.apply(lambda x: x[2])
    df['matched_visitors'] = results.apply(lambda x: x[3])
    df['pct_visitors_matched'] = np.where(
        df['total_visitors'] > 0,
        (df['matched_visitors'] / df['total_visitors']) * 100,
        0
    )

    df = df.drop(columns=['visitor_home_cbgs'])

    df = df[df['total_visitors'] > 0]
    logger.info(f"Output: {len(df):,} rows with visitors")

    return df


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file_index>")
        sys.exit(1)

    try:
        file_index = int(sys.argv[1])
    except ValueError:
        logger.error(f"Invalid file index: {sys.argv[1]}")
        sys.exit(1)

    with open(FILE_LIST_PATH) as f:
        file_list = [line.strip() for line in f]

    if file_index < 1 or file_index > len(file_list):
        logger.error(f"File index {file_index} out of range (1-{len(file_list)})")
        sys.exit(1)

    file_path = Path(file_list[file_index - 1])
    logger.info(f"Task {file_index}: {file_path.name}")

    load_lookups()

    df = process_file(file_path)

    if df is None or len(df) == 0:
        logger.warning("No output data")
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_name = file_path.name.replace('.csv.gz', '.parquet')
    output_path = OUTPUT_DIR / output_name

    df.to_parquet(output_path, index=False, compression='snappy')
    logger.info(f"Saved to {output_path}")

    if df['rep_lean_2020'].notna().any():
        logger.info(f"Rep lean 2020: mean={df['rep_lean_2020'].mean():.3f}, "
                    f"range=[{df['rep_lean_2020'].min():.3f}, {df['rep_lean_2020'].max():.3f}]")
    else:
        logger.warning("No matched CBGs - all rep_lean values are NaN")
    logger.info(f"Match rate: mean={df['pct_visitors_matched'].mean():.1f}%")


if __name__ == "__main__":
    main()
