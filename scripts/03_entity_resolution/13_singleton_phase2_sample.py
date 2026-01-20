#!/usr/bin/env python3
"""
Phase 2: Sample candidate pairs for labeling.

Stratified sampling across similarity distribution to ensure training data
covers easy matches, hard cases, and clear non-matches.

Usage: python 13_singleton_phase2_sample.py --msa columbus_oh --n_samples 1000
"""

import argparse
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
INPUT_DIR = PROJECT_DIR / "outputs" / "singleton_matching"
OUTPUT_DIR = INPUT_DIR / "training_samples"


def stratified_sample(df: pd.DataFrame, n_samples: int, strata_col: str = 'cos_sim') -> pd.DataFrame:
    """
    Sample pairs stratified by similarity score.

    Strata:
      - High (0.90-1.00): Likely matches - need to verify
      - Medium-high (0.80-0.90): Uncertain - most informative
      - Medium (0.70-0.80): Probably non-matches but worth checking
      - Low (0.60-0.70): Likely non-matches - sanity check
      - Very low (<0.60): Clear non-matches - small sample for baseline
    """
    strata = [
        ('high', 0.90, 1.01, 0.25),        # 25% from high similarity
        ('medium_high', 0.80, 0.90, 0.30), # 30% from medium-high (most informative)
        ('medium', 0.70, 0.80, 0.25),      # 25% from medium
        ('low', 0.60, 0.70, 0.15),         # 15% from low
        ('very_low', 0.0, 0.60, 0.05),     # 5% from very low
    ]

    samples = []

    for stratum_name, low, high, proportion in strata:
        stratum_df = df[(df[strata_col] >= low) & (df[strata_col] < high)]
        n_stratum = int(n_samples * proportion)

        if len(stratum_df) == 0:
            print(f"  Warning: No pairs in stratum {stratum_name} ({low:.2f}-{high:.2f})")
            continue

        n_actual = min(n_stratum, len(stratum_df))
        sampled = stratum_df.sample(n=n_actual, random_state=42)
        sampled['stratum'] = stratum_name
        samples.append(sampled)

        print(f"  {stratum_name} ({low:.2f}-{high:.2f}): {len(stratum_df):,} available, sampled {n_actual}")

    result = pd.concat(samples, ignore_index=True)

    # If we're short, fill from medium_high (most informative)
    if len(result) < n_samples:
        shortfall = n_samples - len(result)
        already_sampled = set(result.index)
        medium_high = df[(df[strata_col] >= 0.80) & (df[strata_col] < 0.90)]
        available = medium_high[~medium_high.index.isin(already_sampled)]

        if len(available) >= shortfall:
            extra = available.sample(n=shortfall, random_state=43)
            extra['stratum'] = 'medium_high_extra'
            result = pd.concat([result, extra], ignore_index=True)
            print(f"  Added {shortfall} extra samples from medium_high")

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--msa', required=True, help='MSA name (e.g., columbus_oh)')
    parser.add_argument('--n_samples', type=int, default=1000, help='Number of pairs to sample')
    args = parser.parse_args()

    msa = args.msa
    n_samples = args.n_samples

    print("=" * 70)
    print(f"Phase 2: Sample Pairs for Labeling - {msa}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_file = INPUT_DIR / f"{msa}_candidate_pairs.parquet"
    if not input_file.exists():
        raise FileNotFoundError(f"Candidate pairs not found: {input_file}")

    print(f"\n[1] Loading candidate pairs from {input_file.name}...")
    df = pd.read_parquet(input_file)
    print(f"  Total candidate pairs: {len(df):,}")

    print(f"\n[2] Similarity distribution:")
    print(f"  cos_sim:      min={df['cos_sim'].min():.3f}, max={df['cos_sim'].max():.3f}, "
          f"mean={df['cos_sim'].mean():.3f}, median={df['cos_sim'].median():.3f}")
    print(f"  jaro_winkler: min={df['jaro_winkler'].min():.3f}, max={df['jaro_winkler'].max():.3f}, "
          f"mean={df['jaro_winkler'].mean():.3f}")

    # Distribution by buckets
    print(f"\n  Distribution by cos_sim bucket:")
    buckets = [(0.9, 1.0), (0.8, 0.9), (0.7, 0.8), (0.6, 0.7), (0.0, 0.6)]
    for low, high in buckets:
        count = len(df[(df['cos_sim'] >= low) & (df['cos_sim'] < high)])
        pct = 100 * count / len(df)
        print(f"    {low:.1f}-{high:.1f}: {count:,} ({pct:.1f}%)")

    print(f"\n[3] Stratified sampling ({n_samples} pairs)...")
    sampled = stratified_sample(df, n_samples)
    print(f"  Total sampled: {len(sampled):,}")

    # Shuffle the sample so strata are mixed
    sampled = sampled.sample(frac=1, random_state=44).reset_index(drop=True)

    # Add sample_id for easy reference
    sampled['sample_id'] = range(1, len(sampled) + 1)

    # Select columns for labeling
    label_cols = [
        'sample_id',
        'location_name',
        'company_name',
        'cos_sim',
        'jaro_winkler',
        'token_jaccard',
        'contains_match',
        'stratum',
        'n_pois',
    ]

    # Keep full data for later joining
    sampled_full = sampled.copy()
    sampled_for_labeling = sampled[label_cols].copy()

    print(f"\n[4] Saving outputs...")

    # Full sample with all columns (for later use)
    full_output = OUTPUT_DIR / f"{msa}_sample_full.parquet"
    sampled_full.to_parquet(full_output, index=False)
    print(f"  Full sample: {full_output}")

    # Labeling file (cleaner, for display)
    label_output = OUTPUT_DIR / f"{msa}_sample_for_labeling.parquet"
    sampled_for_labeling.to_parquet(label_output, index=False)
    print(f"  Labeling sample: {label_output}")

    # CSV for easy viewing
    csv_output = OUTPUT_DIR / f"{msa}_sample_for_labeling.csv"
    sampled_for_labeling.to_csv(csv_output, index=False)
    print(f"  CSV version: {csv_output}")

    print(f"\n[5] Sample summary by stratum:")
    stratum_summary = sampled.groupby('stratum').agg({
        'cos_sim': ['count', 'mean', 'min', 'max'],
        'jaro_winkler': 'mean'
    }).round(3)
    print(stratum_summary.to_string())

    print(f"\n[6] Preview of sampled pairs:")
    preview = sampled_for_labeling.head(20)[['sample_id', 'location_name', 'company_name', 'cos_sim', 'jaro_winkler']]
    print(preview.to_string(index=False))

    print("\n" + "=" * 70)
    print("Phase 2 complete!")
    print(f"Ready for labeling: {len(sampled)} pairs")
    print("=" * 70)


if __name__ == '__main__':
    main()
