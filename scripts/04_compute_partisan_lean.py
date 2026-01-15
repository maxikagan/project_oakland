#!/usr/bin/env python3
"""
Step 4: Parse visitor CBGs and compute partisan lean by POI-month.

This is an array job script. It:
1. Reads filtered Advan data for a state
2. Reads national CBG partisan lean lookup (both 2016 and 2020)
3. For each POI-month:
   - Parses visitor_home_cbgs JSON
   - Looks up partisan lean for each CBG (both years)
   - Computes weighted average rep_lean_2020 and rep_lean_2016
   - Tracks unmatched CBGs
4. Generates state-level output with diagnostic columns

Usage:
  python3 04_compute_partisan_lean.py <STATE>

Example:
  python3 04_compute_partisan_lean.py CA

Output: /global/scratch/users/maxkagan/project_oakland/intermediate/advan_partisan/{STATE}.parquet
Diagnostics: /global/scratch/users/maxkagan/project_oakland/intermediate/unmatched_cbgs/{STATE}.parquet
"""

import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

FILTERED_DATA_DIR = Path("/global/scratch/users/maxkagan/project_oakland/intermediate/advan_filtered")
CBG_LOOKUP_PATH = Path("/global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national_both_years.parquet")
OUTPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/intermediate/advan_partisan")
DIAGNOSTIC_DIR = Path("/global/scratch/users/maxkagan/project_oakland/intermediate/unmatched_cbgs")

CBG_DICT_2020 = None
CBG_DICT_2016 = None


def load_cbg_lookup():
    """Load national CBG partisan lean lookup table as dicts for fast lookup."""
    global CBG_DICT_2020, CBG_DICT_2016

    logger.info("Loading national CBG lookup...")

    if not CBG_LOOKUP_PATH.exists():
        logger.error(f"CBG lookup not found at {CBG_LOOKUP_PATH}")
        return False

    try:
        cbg_df = pd.read_parquet(CBG_LOOKUP_PATH)
        logger.info(f"Loaded {len(cbg_df)} CBGs from lookup table")

        CBG_DICT_2020 = dict(zip(cbg_df['GEOID'].astype(str), cbg_df['two_party_rep_share_2020']))
        CBG_DICT_2016 = dict(zip(cbg_df['GEOID'].astype(str), cbg_df['two_party_rep_share_2016']))

        logger.info(f"Built lookup dicts with {len(CBG_DICT_2020)} entries")
        return True
    except Exception as e:
        logger.error(f"Failed to load CBG lookup: {e}")
        return False


def parse_visitor_cbgs(visitor_cbgs_json):
    """Parse visitor_home_cbgs JSON string into dict."""
    if pd.isna(visitor_cbgs_json) or visitor_cbgs_json is None:
        return {}

    if isinstance(visitor_cbgs_json, dict):
        return visitor_cbgs_json

    try:
        return json.loads(visitor_cbgs_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def compute_partisan_lean_for_row(visitor_cbgs_json):
    """Compute weighted average partisan lean for a single POI (both 2016 and 2020)."""
    visitor_cbgs_dict = parse_visitor_cbgs(visitor_cbgs_json)

    if not visitor_cbgs_dict:
        return np.nan, np.nan, 0, 0

    total_visitors = 0
    weighted_rep_2020 = 0.0
    weighted_rep_2016 = 0.0
    matched_visitors = 0

    for cbg_geoid, visitor_count in visitor_cbgs_dict.items():
        try:
            visitor_count = int(visitor_count)
        except (ValueError, TypeError):
            continue

        cbg_str = str(cbg_geoid).zfill(12)
        total_visitors += visitor_count

        if cbg_str in CBG_DICT_2020:
            rep_share_2020 = CBG_DICT_2020[cbg_str]
            rep_share_2016 = CBG_DICT_2016.get(cbg_str, 0.5)
            weighted_rep_2020 += rep_share_2020 * visitor_count
            weighted_rep_2016 += rep_share_2016 * visitor_count
            matched_visitors += visitor_count

    if matched_visitors == 0:
        return np.nan, np.nan, total_visitors, 0

    rep_lean_2020 = weighted_rep_2020 / matched_visitors
    rep_lean_2016 = weighted_rep_2016 / matched_visitors

    return rep_lean_2020, rep_lean_2016, total_visitors, matched_visitors


def process_chunk(chunk_data):
    """Process a chunk of rows."""
    results = []

    for _, row in chunk_data.iterrows():
        rep_lean_2020, rep_lean_2016, total_visitors, matched_visitors = compute_partisan_lean_for_row(
            row['visitor_home_cbgs']
        )

        if total_visitors == 0:
            continue

        pct_matched = (matched_visitors / total_visitors * 100) if total_visitors > 0 else np.nan

        result_row = {
            'placekey': row['placekey'],
            'date_range_start': row['date_range_start'],
            'brand': row['brand'],
            'top_category': row['top_category'],
            'sub_category': row['sub_category'],
            'naics_code': row['naics_code'],
            'city': row['city'],
            'region': row['region'],
            'poi_cbg': row['poi_cbg'],
            'cbsa_title': row.get('cbsa_title'),
            'parent_placekey': row['parent_placekey'],
            'median_dwell': row['median_dwell'],
            'rep_lean_2020': rep_lean_2020,
            'rep_lean_2016': rep_lean_2016,
            'total_visitors': total_visitors,
            'matched_visitors': matched_visitors,
            'pct_visitors_matched': pct_matched
        }

        results.append(result_row)

    return results


def process_state(state):
    """Compute partisan lean for all POIs in a state."""
    logger.info(f"Processing state: {state}")

    input_dir = FILTERED_DATA_DIR / state
    input_file = input_dir / f"advan_{state}_filtered.parquet"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return False

    try:
        df = pd.read_parquet(input_file)
        logger.info(f"{state}: Loaded {len(df):,} POI-month observations")
    except Exception as e:
        logger.error(f"{state}: Failed to load input data: {e}")
        return False

    logger.info(f"{state}: Computing partisan lean using vectorized apply...")

    df['_result'] = df['visitor_home_cbgs'].apply(compute_partisan_lean_for_row)

    df['rep_lean_2020'] = df['_result'].apply(lambda x: x[0])
    df['rep_lean_2016'] = df['_result'].apply(lambda x: x[1])
    df['total_visitors'] = df['_result'].apply(lambda x: x[2])
    df['matched_visitors'] = df['_result'].apply(lambda x: x[3])
    df = df.drop(columns=['_result'])

    df = df[df['total_visitors'] > 0].copy()

    df['pct_visitors_matched'] = (df['matched_visitors'] / df['total_visitors'] * 100)

    results_df = df[[
        'placekey', 'date_range_start', 'brand', 'top_category', 'sub_category',
        'naics_code', 'city', 'region', 'poi_cbg', 'cbsa_title', 'parent_placekey',
        'median_dwell', 'rep_lean_2020', 'rep_lean_2016', 'total_visitors',
        'matched_visitors', 'pct_visitors_matched'
    ]].copy()

    logger.info(f"{state}: {len(results_df):,} observations with valid visitor data")

    if len(results_df) == 0:
        logger.warning(f"{state}: No valid results")
        return True

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        output_file = OUTPUT_DIR / f"{state}.parquet"
        results_df.to_parquet(output_file, index=False, compression='snappy')
        logger.info(f"{state}: Saved to {output_file}")

        logger.info(f"{state}: rep_lean_2020 range: {results_df['rep_lean_2020'].min():.4f} to {results_df['rep_lean_2020'].max():.4f}")
        logger.info(f"{state}: rep_lean_2016 range: {results_df['rep_lean_2016'].min():.4f} to {results_df['rep_lean_2016'].max():.4f}")
        logger.info(f"{state}: avg rep_lean_2020: {results_df['rep_lean_2020'].mean():.4f}")
        logger.info(f"{state}: correlation 2016-2020: {results_df['rep_lean_2016'].corr(results_df['rep_lean_2020']):.4f}")
        logger.info(f"{state}: % visitors matched: {results_df['pct_visitors_matched'].mean():.2f}%")
    except Exception as e:
        logger.error(f"{state}: Failed to save output: {e}")
        return False

    return True


def main():
    """Run Step 4 for specified state."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <STATE>")
        print(f"Example: {sys.argv[0]} CA")
        sys.exit(1)

    state = sys.argv[1].upper()

    if not state.isalpha() or len(state) != 2:
        logger.error(f"Invalid state code: {state}")
        sys.exit(1)

    if not load_cbg_lookup():
        logger.error("Failed to load CBG lookup")
        sys.exit(1)

    success = process_state(state)

    if success:
        logger.info(f"Step 4 complete for {state}")
        sys.exit(0)
    else:
        logger.error(f"Step 4 failed for {state}")
        sys.exit(1)


if __name__ == "__main__":
    main()
