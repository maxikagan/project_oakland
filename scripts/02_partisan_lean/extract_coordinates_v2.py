#!/usr/bin/env python3
"""
Extract POI coordinates (latitude, longitude) from raw Advan data.
Optimized version with parallel processing and chunked output.

Creates a deduplicated lookup table: placekey → (latitude, longitude)

Usage:
    python3 extract_coordinates_v2.py [--workers N] [--chunk-size N]

Output:
    outputs/poi_coordinates.parquet - deduplicated placekey → lat/lon mapping
"""

import pandas as pd
from pathlib import Path
import logging
import sys
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import tempfile
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("/global/scratch/users/maxkagan/01_foot_traffic_location/advan/foot_traffic_monthly_complete_2026-01-12/monthly-patterns-foot-traffic")
OUTPUT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs")
OUTPUT_PATH = OUTPUT_DIR / "poi_coordinates.parquet"

COLUMNS_TO_READ = ['PLACEKEY', 'LATITUDE', 'LONGITUDE']


def process_single_file(filepath: Path) -> pd.DataFrame:
    """Process a single file and return coordinates dataframe."""
    try:
        df = pd.read_csv(
            filepath,
            compression='gzip',
            usecols=COLUMNS_TO_READ,
            dtype={'PLACEKEY': str, 'LATITUDE': float, 'LONGITUDE': float}
        )
        df.columns = df.columns.str.lower()
        df = df.dropna(subset=['placekey', 'latitude', 'longitude'])
        df = df.drop_duplicates(subset=['placekey'], keep='first')
        return df
    except Exception as e:
        logger.warning(f"Error processing {filepath.name}: {e}")
        return pd.DataFrame(columns=['placekey', 'latitude', 'longitude'])


def process_chunk(files: list, chunk_id: int, temp_dir: Path) -> tuple:
    """Process a chunk of files and write intermediate parquet."""
    chunk_dfs = []
    for f in files:
        df = process_single_file(f)
        if len(df) > 0:
            chunk_dfs.append(df)

    if not chunk_dfs:
        return chunk_id, 0, None

    chunk_df = pd.concat(chunk_dfs, ignore_index=True)
    chunk_df = chunk_df.drop_duplicates(subset=['placekey'], keep='first')

    output_path = temp_dir / f"chunk_{chunk_id:04d}.parquet"
    chunk_df.to_parquet(output_path, index=False)

    return chunk_id, len(chunk_df), output_path


def main():
    parser = argparse.ArgumentParser(description='Extract POI coordinates')
    parser.add_argument('--workers', type=int, default=8, help='Number of parallel workers')
    parser.add_argument('--chunk-size', type=int, default=50, help='Files per chunk')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Extracting POI coordinates (optimized v2)")
    logger.info(f"Workers: {args.workers}, Chunk size: {args.chunk_size}")
    logger.info("=" * 60)

    files = sorted(RAW_DATA_DIR.glob("*.csv.gz"))
    logger.info(f"Found {len(files)} raw Advan files")

    if not files:
        logger.error("No files found!")
        return 1

    chunks = [files[i:i + args.chunk_size] for i in range(0, len(files), args.chunk_size)]
    logger.info(f"Split into {len(chunks)} chunks of ~{args.chunk_size} files each")

    Path("/global/scratch/users/maxkagan/tmp").mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="coords_", dir="/global/scratch/users/maxkagan/tmp"))
    logger.info(f"Temp directory: {temp_dir}")

    try:
        chunk_paths = []
        total_rows = 0

        logger.info(f"Processing {len(chunks)} chunks with {args.workers} workers...")

        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_chunk, chunk, i, temp_dir): i
                for i, chunk in enumerate(chunks)
            }

            completed = 0
            for future in as_completed(futures):
                chunk_id, n_rows, path = future.result()
                completed += 1
                if path:
                    chunk_paths.append(path)
                    total_rows += n_rows

                if completed % 10 == 0 or completed == len(chunks):
                    logger.info(f"Completed {completed}/{len(chunks)} chunks ({total_rows:,} rows so far)")

        logger.info(f"All chunks processed. Merging {len(chunk_paths)} intermediate files...")

        if not chunk_paths:
            logger.error("No chunks produced any valid data! Check source file format.")
            return 1

        coords_df = pd.concat(
            (pd.read_parquet(path) for path in sorted(chunk_paths)),
            ignore_index=True
        )
        logger.info(f"Before final dedup: {len(coords_df):,} rows")

        coords_df = coords_df.drop_duplicates(subset=['placekey'], keep='first')
        logger.info(f"After final dedup: {len(coords_df):,} unique POIs")

        logger.info(f"Latitude range: [{coords_df['latitude'].min():.4f}, {coords_df['latitude'].max():.4f}]")
        logger.info(f"Longitude range: [{coords_df['longitude'].min():.4f}, {coords_df['longitude'].max():.4f}]")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        coords_df.to_parquet(OUTPUT_PATH, index=False, compression='snappy')
        logger.info(f"Saved to {OUTPUT_PATH}")

        file_size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.1f} MB")

    finally:
        logger.info(f"Cleaning up temp directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

    logger.info("=" * 60)
    logger.info("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
