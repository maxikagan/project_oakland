#!/usr/bin/env python3
"""
Analyze SafeGraph Spend data overlap with partisan lean data.
Answers:
1. How many unique placekeys are in SafeGraph Spend?
2. What's the overlap with partisan lean data?
3. What does the joint distribution look like?
"""

import pandas as pd
import glob
import os
import json
import sys

SPEND_DIR = "/global/scratch/users/maxkagan/01_foot_traffic_location/safegraph/safegraph_spend/dewey_2024_10_21/"
PARTISAN_LEAN_DIR = "/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national/"
OUTPUT_DIR = "/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/spend_analysis/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print("=" * 60)
    print("SAFEGRAPH SPEND DATA ANALYSIS")
    print("=" * 60)

    # 0. First check that data exists
    print("\n0. Checking data availability...")

    spend_files = sorted(glob.glob(f"{SPEND_DIR}*.csv.gz"))
    print(f"   Spend files found: {len(spend_files)}")

    partisan_files = sorted(glob.glob(f"{PARTISAN_LEAN_DIR}partisan_lean_*.parquet"))
    print(f"   Partisan lean files found: {len(partisan_files)}")

    if len(spend_files) == 0:
        print("   ERROR: No spend files found!")
        return 1

    if len(partisan_files) == 0:
        print("   ERROR: No partisan lean files found!")
        return 1

    # 0b. Check schemas
    print("\n   Checking schemas...")

    # Spend schema (from first few rows)
    sample_spend = pd.read_csv(spend_files[0], compression='gzip', nrows=2)
    print(f"   Spend columns: {sample_spend.columns.tolist()}")

    # Partisan schema
    sample_partisan = pd.read_parquet(partisan_files[0], engine='pyarrow')
    print(f"   Partisan columns: {sample_partisan.columns.tolist()}")

    # Identify the placekey column in partisan data
    partisan_pk_col = None
    for col in sample_partisan.columns:
        if 'placekey' in col.lower():
            partisan_pk_col = col
            break

    if partisan_pk_col is None:
        print("   ERROR: No placekey column found in partisan data!")
        print(f"   Available columns: {sample_partisan.columns.tolist()}")
        return 1

    print(f"   Using partisan placekey column: '{partisan_pk_col}'")

    # Identify the rep share column
    rep_share_col = None
    for col in sample_partisan.columns:
        if 'rep' in col.lower() and 'share' in col.lower():
            rep_share_col = col
            break

    if rep_share_col is None:
        # Try alternative names
        for col in sample_partisan.columns:
            if 'rep' in col.lower() and ('lean' in col.lower() or 'weighted' in col.lower()):
                rep_share_col = col
                break

    if rep_share_col is None:
        print("   WARNING: No obvious rep share column found")
        print(f"   Available columns: {sample_partisan.columns.tolist()}")
        # Use the first numeric column that's not placekey
        for col in sample_partisan.columns:
            if col != partisan_pk_col and sample_partisan[col].dtype in ['float64', 'float32']:
                rep_share_col = col
                print(f"   Using '{rep_share_col}' as rep share column")
                break

    if rep_share_col is None:
        print("   ERROR: Could not identify rep share column!")
        return 1

    print(f"   Using rep share column: '{rep_share_col}'")

    # 1. Count unique placekeys in spend data (sample months)
    print("\n" + "=" * 60)
    print("1. COUNTING UNIQUE PLACEKEYS IN SPEND DATA")
    print("=" * 60)

    # Sample 3 months spread across the data
    sample_months = ["2019-06-01", "2021-06-01", "2023-06-01"]

    all_spend_placekeys = set()
    month_counts = {}

    for month in sample_months:
        month_files = [f for f in spend_files if f"SPEND_DATE_RANGE_START-{month}" in f]
        print(f"\n   Processing {month}: {len(month_files)} files")

        month_pks = set()
        for f in month_files:
            df = pd.read_csv(f, compression='gzip', usecols=['PLACEKEY'], dtype=str)
            month_pks.update(df['PLACEKEY'].dropna().unique())

        month_counts[month] = len(month_pks)
        all_spend_placekeys.update(month_pks)
        print(f"   Unique placekeys in {month}: {len(month_pks):,}")

    print(f"\n   Total unique placekeys (union of 3 months): {len(all_spend_placekeys):,}")

    # 2. Load all partisan lean placekeys
    print("\n" + "=" * 60)
    print("2. LOADING PARTISAN LEAN DATA")
    print("=" * 60)

    partisan_placekeys = set()

    for i, f in enumerate(partisan_files):
        df = pd.read_parquet(f, columns=[partisan_pk_col], engine='pyarrow')
        partisan_placekeys.update(df[partisan_pk_col].dropna().unique())
        if (i + 1) % 20 == 0:
            print(f"   Processed {i + 1}/{len(partisan_files)} files...")

    print(f"   Total unique placekeys in partisan data: {len(partisan_placekeys):,}")

    # 3. Check overlap
    print("\n" + "=" * 60)
    print("3. CHECKING OVERLAP")
    print("=" * 60)

    overlap = all_spend_placekeys & partisan_placekeys
    spend_only = all_spend_placekeys - partisan_placekeys
    partisan_only = partisan_placekeys - all_spend_placekeys

    print(f"\n   Placekeys in BOTH datasets: {len(overlap):,}")
    print(f"   Placekeys in Spend ONLY: {len(spend_only):,}")
    print(f"   Placekeys in Partisan ONLY: {len(partisan_only):,}")

    if len(all_spend_placekeys) > 0:
        print(f"\n   Overlap rate (of spend): {100 * len(overlap) / len(all_spend_placekeys):.1f}%")
    if len(partisan_placekeys) > 0:
        print(f"   Overlap rate (of partisan): {100 * len(overlap) / len(partisan_placekeys):.1f}%")

    if len(overlap) == 0:
        print("\n   ERROR: No overlapping placekeys! Cannot proceed with joint analysis.")
        # Save what we have
        summary = {
            'spend_unique_placekeys': len(all_spend_placekeys),
            'partisan_unique_placekeys': len(partisan_placekeys),
            'overlap_placekeys': 0,
            'error': 'No overlap between datasets'
        }
        with open(f"{OUTPUT_DIR}spend_overlap_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        return 1

    # 4. Sample joint distribution
    print("\n" + "=" * 60)
    print("4. SAMPLING JOINT DISTRIBUTION")
    print("=" * 60)

    # Load a recent month of spend with full data for overlapping placekeys
    recent_month = "2023-06-01"
    recent_spend_files = [f for f in spend_files if f"SPEND_DATE_RANGE_START-{recent_month}" in f]
    print(f"\n   Loading spend data for {recent_month} ({len(recent_spend_files)} files)...")

    spend_chunks = []
    for f in recent_spend_files:
        df = pd.read_csv(f, compression='gzip', dtype={
            'PLACEKEY': str,
            'RAW_TOTAL_SPEND': float,
            'RAW_NUM_TRANSACTIONS': float,
            'RAW_NUM_CUSTOMERS': float,
            'BRANDS': str
        }, usecols=['PLACEKEY', 'RAW_TOTAL_SPEND', 'RAW_NUM_TRANSACTIONS', 'RAW_NUM_CUSTOMERS', 'BRANDS'])
        # Filter to overlap immediately to save memory
        df = df[df['PLACEKEY'].isin(overlap)]
        spend_chunks.append(df)

    spend_df = pd.concat(spend_chunks, ignore_index=True)
    print(f"   Loaded {len(spend_df):,} spend records (filtered to overlap)")

    # Load corresponding partisan lean (just one month for this analysis)
    print(f"   Loading partisan lean data...")

    # Find a matching month
    partisan_file_2023_06 = [f for f in partisan_files if '2023-06' in f or '2023-07' in f]
    if len(partisan_file_2023_06) == 0:
        partisan_file_2023_06 = partisan_files[-1:]  # Use most recent

    partisan_df = pd.read_parquet(partisan_file_2023_06[0], engine='pyarrow')
    partisan_df = partisan_df[partisan_df[partisan_pk_col].isin(overlap)]
    print(f"   Loaded {len(partisan_df):,} partisan records (filtered to overlap)")

    # Merge
    print(f"   Merging datasets...")
    merged = spend_df.merge(
        partisan_df[[partisan_pk_col, rep_share_col]],
        left_on='PLACEKEY',
        right_on=partisan_pk_col,
        how='inner'
    )

    print(f"   Merged records: {len(merged):,}")

    if len(merged) == 0:
        print("   ERROR: Merge resulted in 0 records!")
        return 1

    # 5. Summary statistics
    print("\n" + "=" * 60)
    print("5. JOINT DISTRIBUTION SUMMARY")
    print("=" * 60)

    print(f"\n   SPENDING SUMMARY:")
    print(f"      Mean RAW_TOTAL_SPEND: ${merged['RAW_TOTAL_SPEND'].mean():,.2f}")
    print(f"      Median RAW_TOTAL_SPEND: ${merged['RAW_TOTAL_SPEND'].median():,.2f}")
    print(f"      Std RAW_TOTAL_SPEND: ${merged['RAW_TOTAL_SPEND'].std():,.2f}")
    print(f"      Mean transactions: {merged['RAW_NUM_TRANSACTIONS'].mean():,.1f}")
    print(f"      Mean customers: {merged['RAW_NUM_CUSTOMERS'].mean():,.1f}")

    print(f"\n   PARTISAN LEAN SUMMARY:")
    print(f"      Mean rep share: {merged[rep_share_col].mean():.3f}")
    print(f"      Median rep share: {merged[rep_share_col].median():.3f}")
    print(f"      Std rep share: {merged[rep_share_col].std():.3f}")
    print(f"      Min: {merged[rep_share_col].min():.3f}")
    print(f"      Max: {merged[rep_share_col].max():.3f}")

    # Correlation
    corr = merged['RAW_TOTAL_SPEND'].corr(merged[rep_share_col])
    corr_trans = merged['RAW_NUM_TRANSACTIONS'].corr(merged[rep_share_col])
    corr_cust = merged['RAW_NUM_CUSTOMERS'].corr(merged[rep_share_col])

    print(f"\n   CORRELATIONS:")
    print(f"      Spend vs rep_share: {corr:.3f}")
    print(f"      Transactions vs rep_share: {corr_trans:.3f}")
    print(f"      Customers vs rep_share: {corr_cust:.3f}")

    # By quartile
    print(f"\n   SPENDING BY PARTISAN QUARTILE:")
    try:
        merged['rep_quartile'] = pd.qcut(
            merged[rep_share_col],
            4,
            labels=['Q1 (Dem)', 'Q2', 'Q3', 'Q4 (Rep)'],
            duplicates='drop'
        )

        quartile_stats = merged.groupby('rep_quartile', observed=True).agg({
            'RAW_TOTAL_SPEND': ['mean', 'median', 'count'],
            'RAW_NUM_CUSTOMERS': 'mean'
        }).round(2)
        print(quartile_stats.to_string())

    except ValueError as e:
        print(f"      Warning: Could not create quartiles: {e}")

    # Top brands by overlap
    print(f"\n   TOP 10 BRANDS BY RECORD COUNT (in overlap):")
    brand_counts = merged['BRANDS'].value_counts().head(10)
    for brand, count in brand_counts.items():
        brand_spend = merged[merged['BRANDS'] == brand]['RAW_TOTAL_SPEND'].mean()
        brand_rep = merged[merged['BRANDS'] == brand][rep_share_col].mean()
        print(f"      {brand}: {count:,} records, avg spend ${brand_spend:,.0f}, avg rep share {brand_rep:.2f}")

    # 6. Save outputs
    print("\n" + "=" * 60)
    print("6. SAVING OUTPUTS")
    print("=" * 60)

    # Save sample
    sample_size = min(50000, len(merged))
    sample_output = merged.sample(sample_size)[['PLACEKEY', 'BRANDS', 'RAW_TOTAL_SPEND', 'RAW_NUM_TRANSACTIONS', 'RAW_NUM_CUSTOMERS', rep_share_col]]
    sample_output.to_parquet(f"{OUTPUT_DIR}spend_partisan_sample.parquet", index=False)
    print(f"   Saved {sample_size:,} sample records to spend_partisan_sample.parquet")

    # Save summary
    summary = {
        'spend_unique_placekeys_3months': len(all_spend_placekeys),
        'spend_placekeys_by_month': month_counts,
        'partisan_unique_placekeys': len(partisan_placekeys),
        'overlap_placekeys': len(overlap),
        'overlap_rate_of_spend': len(overlap) / len(all_spend_placekeys) if len(all_spend_placekeys) > 0 else 0,
        'overlap_rate_of_partisan': len(overlap) / len(partisan_placekeys) if len(partisan_placekeys) > 0 else 0,
        'merged_records': len(merged),
        'mean_spend': float(merged['RAW_TOTAL_SPEND'].mean()),
        'median_spend': float(merged['RAW_TOTAL_SPEND'].median()),
        'mean_rep_share': float(merged[rep_share_col].mean()),
        'correlation_spend_rep_share': float(corr),
        'correlation_transactions_rep_share': float(corr_trans),
        'correlation_customers_rep_share': float(corr_cust),
        'rep_share_column_used': rep_share_col,
        'partisan_placekey_column_used': partisan_pk_col,
    }

    with open(f"{OUTPUT_DIR}spend_overlap_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   Saved summary to spend_overlap_summary.json")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
