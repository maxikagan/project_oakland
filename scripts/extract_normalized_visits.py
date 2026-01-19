#!/usr/bin/env python3
"""
Extract NORMALIZED_VISITS_BY_STATE_SCALING from raw Advan CSVs.

Processes all csv.gz files and outputs a parquet with just the columns needed
to join back to existing partisan lean data.

Designed for SLURM array jobs (one task per file).

Usage:
    python3 extract_normalized_visits.py <file_index>
"""

import sys
import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
FILE_LIST_PATH = PROJECT_DIR / "inputs" / "advan_file_list.txt"
OUTPUT_DIR = PROJECT_DIR / "intermediate" / "normalized_visits_by_file"

COLUMNS_TO_READ = [
    'PLACEKEY',
    'DATE_RANGE_START',
    'NORMALIZED_VISITS_BY_STATE_SCALING'
]


def process_file(file_path: Path):
    """Extract normalized visits from a single csv.gz file."""
    logger.info(f"Reading {file_path.name}...")

    df = pd.read_csv(
        file_path,
        compression='gzip',
        usecols=COLUMNS_TO_READ,
        dtype={'PLACEKEY': str}
    )
    logger.info(f"Read {len(df):,} rows")

    if len(df) == 0:
        return None

    df.columns = df.columns.str.lower()

    df = df.dropna(subset=['normalized_visits_by_state_scaling'])
    logger.info(f"After dropping nulls: {len(df):,} rows")

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

    df = process_file(file_path)

    if df is None or len(df) == 0:
        logger.warning("No output data")
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_name = file_path.name.replace('.csv.gz', '.parquet')
    output_path = OUTPUT_DIR / output_name

    df.to_parquet(output_path, index=False, compression='snappy')
    logger.info(f"Saved to {output_path}")

    logger.info(f"Normalized visits: mean={df['normalized_visits_by_state_scaling'].mean():.1f}, "
                f"median={df['normalized_visits_by_state_scaling'].median():.1f}")


if __name__ == "__main__":
    main()
