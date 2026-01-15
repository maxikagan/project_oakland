#!/usr/bin/env python3
"""
Combine all partisan lean parquet files into final output.

Reads all files from intermediate/partisan_lean_by_file/
Outputs combined dataset partitioned by month.
Generates summary diagnostics.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/intermediate/partisan_lean_by_file")
OUTPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/outputs/national")
DIAGNOSTICS_DIR = Path("/global/home/users/maxkagan/project_oakland/outputs/diagnostics")


def count_input_files():
    """Count available input files."""
    files = list(INPUT_DIR.glob("*.parquet"))
    logger.info(f"Found {len(files)} parquet files to combine")
    return files


def combine_files(files):
    """Combine all parquet files into single DataFrame."""
    logger.info("Reading and combining files...")

    dfs = []
    for i, f in enumerate(sorted(files)):
        df = pd.read_parquet(f)
        dfs.append(df)

        if (i + 1) % 100 == 0:
            logger.info(f"  Read {i + 1}/{len(files)} files")

    logger.info("Concatenating all DataFrames...")
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined shape: {combined.shape}")

    return combined


def add_derived_columns(df):
    """Add useful derived columns."""
    logger.info("Adding derived columns...")

    df['date_range_start'] = pd.to_datetime(df['date_range_start'])
    df['year'] = df['date_range_start'].dt.year
    df['month'] = df['date_range_start'].dt.month
    df['year_month'] = df['date_range_start'].dt.to_period('M').astype(str)

    return df


def save_partitioned(df):
    """Save output partitioned by year-month."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Saving partitioned by year-month...")
    for ym, group in df.groupby('year_month'):
        output_path = OUTPUT_DIR / f"partisan_lean_{ym}.parquet"
        group.to_parquet(output_path, index=False, compression='snappy')
        logger.info(f"  {ym}: {len(group):,} rows")

    full_output = OUTPUT_DIR / "partisan_lean_national_full.parquet"
    logger.info(f"Saving full dataset to {full_output}...")
    df.to_parquet(full_output, index=False, compression='snappy')
    logger.info(f"Full dataset saved: {len(df):,} rows")


def generate_diagnostics(df):
    """Generate summary diagnostics."""
    DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Generating diagnostics...")

    diag = {
        'generated_at': datetime.now().isoformat(),
        'total_rows': len(df),
        'unique_pois': df['placekey'].nunique(),
        'unique_brands': df['brand'].nunique(),
        'states': df['region'].nunique(),
        'date_range': f"{df['date_range_start'].min()} to {df['date_range_start'].max()}",
        'months': df['year_month'].nunique(),
    }

    rep_2020 = df['rep_lean_2020'].dropna()
    diag['rep_lean_2020'] = {
        'count': len(rep_2020),
        'mean': float(rep_2020.mean()),
        'std': float(rep_2020.std()),
        'min': float(rep_2020.min()),
        'median': float(rep_2020.median()),
        'max': float(rep_2020.max()),
    }

    diag['match_rate'] = {
        'mean': float(df['pct_visitors_matched'].mean()),
        'median': float(df['pct_visitors_matched'].median()),
        'pct_above_90': float((df['pct_visitors_matched'] >= 90).mean() * 100),
    }

    logger.info("\n" + "=" * 60)
    logger.info("DIAGNOSTICS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total rows: {diag['total_rows']:,}")
    logger.info(f"Unique POIs: {diag['unique_pois']:,}")
    logger.info(f"Unique brands: {diag['unique_brands']:,}")
    logger.info(f"States: {diag['states']}")
    logger.info(f"Date range: {diag['date_range']}")
    logger.info(f"Months: {diag['months']}")
    logger.info(f"Rep lean 2020 mean: {diag['rep_lean_2020']['mean']:.4f}")
    logger.info(f"Match rate mean: {diag['match_rate']['mean']:.1f}%")
    logger.info("=" * 60)

    state_summary = df.groupby('region').agg({
        'placekey': 'count',
        'rep_lean_2020': 'mean',
        'pct_visitors_matched': 'mean'
    }).rename(columns={
        'placekey': 'poi_months',
        'rep_lean_2020': 'mean_rep_lean',
        'pct_visitors_matched': 'mean_match_rate'
    }).sort_values('poi_months', ascending=False)

    state_summary.to_csv(DIAGNOSTICS_DIR / 'state_summary.csv')
    logger.info(f"State summary saved to {DIAGNOSTICS_DIR / 'state_summary.csv'}")

    brand_summary = df.groupby('brand').agg({
        'placekey': 'count',
        'rep_lean_2020': ['mean', 'std'],
        'pct_visitors_matched': 'mean'
    })
    brand_summary.columns = ['poi_months', 'mean_rep_lean', 'std_rep_lean', 'mean_match_rate']
    brand_summary = brand_summary.sort_values('poi_months', ascending=False)

    brand_summary.head(500).to_csv(DIAGNOSTICS_DIR / 'brand_summary_top500.csv')
    logger.info(f"Brand summary saved to {DIAGNOSTICS_DIR / 'brand_summary_top500.csv'}")

    return diag


def main():
    logger.info("Starting combine step...")

    files = count_input_files()

    if len(files) < 2096:
        logger.warning(f"Expected 2096 files, found {len(files)}. Some tasks may still be running.")

    if len(files) == 0:
        logger.error("No input files found!")
        return 1

    df = combine_files(files)
    df = add_derived_columns(df)

    save_partitioned(df)

    generate_diagnostics(df)

    logger.info("Combine step complete!")
    return 0


if __name__ == "__main__":
    exit(main())
