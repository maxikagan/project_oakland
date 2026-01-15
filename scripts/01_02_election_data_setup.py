#!/usr/bin/env python3
"""
Step 1-2: Extract election data and build national CBG lookup table with both 2016 and 2020.

This script:
1. Extracts bg-2016-RLCR.csv and bg-2020-RLCR.csv from national Main Method zip
2. Merges on GEOID to create combined lookup
3. Computes two_party_rep_share for both years:
   - 2020: Trump / (Trump + Biden)
   - 2016: Trump / (Trump + Clinton)
4. Handles zero-vote CBGs by setting to 0.5 (neutral)

Output: /global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national_both_years.parquet
"""

import zipfile
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import io

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ELECTION_ZIP = Path("/global/scratch/users/maxkagan/02_election_voter/election_results_geocoded/000 Contiguous USA - Main Method.zip")
OUTPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/inputs")
OUTPUT_FILE = OUTPUT_DIR / "cbg_partisan_lean_national_both_years.parquet"

BG_2020_PATH = "Contiguous USA - Main Method/Block Groups/bg-2020-RLCR.csv"
BG_2016_PATH = "Contiguous USA - Main Method/Block Groups/bg-2016-RLCR.csv"


def extract_and_load_csv(zip_path, csv_internal_path):
    """Extract and load a CSV from within a zip file."""
    logger.info(f"Loading {csv_internal_path} from {zip_path.name}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open(csv_internal_path) as f:
                df = pd.read_csv(f, dtype={'bg_GEOID': str})
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load {csv_internal_path}: {e}")
        return None


def process_2020_data(df):
    """Process 2020 election data."""
    logger.info("Processing 2020 election data...")

    required_cols = ['bg_GEOID', 'G20PRERTRU', 'G20PREDBID']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing columns in 2020 data: {missing}")
        logger.info(f"Available columns: {df.columns.tolist()[:20]}")
        return None

    result = df[['bg_GEOID', 'G20PRERTRU', 'G20PREDBID']].copy()
    result.columns = ['GEOID', 'Trump_2020', 'Biden_2020']

    result['GEOID'] = result['GEOID'].astype(str).str.zfill(12)

    result['Trump_2020'] = pd.to_numeric(result['Trump_2020'], errors='coerce').fillna(0)
    result['Biden_2020'] = pd.to_numeric(result['Biden_2020'], errors='coerce').fillna(0)

    total_votes = result['Trump_2020'] + result['Biden_2020']
    result['two_party_rep_share_2020'] = np.where(
        total_votes > 0,
        result['Trump_2020'] / total_votes,
        0.5
    )

    zero_vote_count = (total_votes == 0).sum()
    if zero_vote_count > 0:
        logger.info(f"2020: {zero_vote_count} CBGs with zero votes set to 0.5")

    logger.info(f"2020 rep share range: {result['two_party_rep_share_2020'].min():.4f} - {result['two_party_rep_share_2020'].max():.4f}")
    logger.info(f"2020 mean rep share: {result['two_party_rep_share_2020'].mean():.4f}")

    return result[['GEOID', 'two_party_rep_share_2020']]


def process_2016_data(df):
    """Process 2016 election data."""
    logger.info("Processing 2016 election data...")

    required_cols = ['bg_GEOID', 'G16PRERTRU', 'G16PREDCLI']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing columns in 2016 data: {missing}")
        logger.info(f"Available columns: {df.columns.tolist()[:20]}")
        return None

    result = df[['bg_GEOID', 'G16PRERTRU', 'G16PREDCLI']].copy()
    result.columns = ['GEOID', 'Trump_2016', 'Clinton_2016']

    result['GEOID'] = result['GEOID'].astype(str).str.zfill(12)

    result['Trump_2016'] = pd.to_numeric(result['Trump_2016'], errors='coerce').fillna(0)
    result['Clinton_2016'] = pd.to_numeric(result['Clinton_2016'], errors='coerce').fillna(0)

    total_votes = result['Trump_2016'] + result['Clinton_2016']
    result['two_party_rep_share_2016'] = np.where(
        total_votes > 0,
        result['Trump_2016'] / total_votes,
        0.5
    )

    zero_vote_count = (total_votes == 0).sum()
    if zero_vote_count > 0:
        logger.info(f"2016: {zero_vote_count} CBGs with zero votes set to 0.5")

    logger.info(f"2016 rep share range: {result['two_party_rep_share_2016'].min():.4f} - {result['two_party_rep_share_2016'].max():.4f}")
    logger.info(f"2016 mean rep share: {result['two_party_rep_share_2016'].mean():.4f}")

    return result[['GEOID', 'two_party_rep_share_2016']]


def main():
    """Run election data setup."""
    logger.info("Starting election data setup...")

    if not ELECTION_ZIP.exists():
        logger.error(f"Election zip not found: {ELECTION_ZIP}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df_2020_raw = extract_and_load_csv(ELECTION_ZIP, BG_2020_PATH)
    if df_2020_raw is None:
        return 1

    df_2016_raw = extract_and_load_csv(ELECTION_ZIP, BG_2016_PATH)
    if df_2016_raw is None:
        return 1

    df_2020 = process_2020_data(df_2020_raw)
    if df_2020 is None:
        return 1

    df_2016 = process_2016_data(df_2016_raw)
    if df_2016 is None:
        return 1

    logger.info("Merging 2016 and 2020 data...")
    combined = pd.merge(df_2020, df_2016, on='GEOID', how='outer')

    combined['two_party_rep_share_2020'] = combined['two_party_rep_share_2020'].fillna(0.5)
    combined['two_party_rep_share_2016'] = combined['two_party_rep_share_2016'].fillna(0.5)

    logger.info(f"Combined dataset: {len(combined)} CBGs")
    logger.info(f"2020-only CBGs: {df_2020['GEOID'].isin(combined['GEOID']).sum() - len(df_2016)}")
    logger.info(f"2016-only CBGs: {df_2016['GEOID'].isin(combined['GEOID']).sum() - len(df_2020)}")

    correlation = combined['two_party_rep_share_2020'].corr(combined['two_party_rep_share_2016'])
    logger.info(f"Correlation between 2016 and 2020 rep share: {correlation:.4f}")

    shift = combined['two_party_rep_share_2020'] - combined['two_party_rep_share_2016']
    logger.info(f"Mean shift (2020 - 2016): {shift.mean():.4f}")
    logger.info(f"Shift range: {shift.min():.4f} to {shift.max():.4f}")

    try:
        combined.to_parquet(OUTPUT_FILE, index=False, compression='snappy')
        logger.info(f"Saved to {OUTPUT_FILE}")
        logger.info(f"Final shape: {combined.shape}")
        logger.info(f"Columns: {combined.columns.tolist()}")
        return 0
    except Exception as e:
        logger.error(f"Failed to save: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
