#!/usr/bin/env python3
"""
Diagnostic script to check distributions for aggregation threshold decisions.
Examines pct_visitors_matched and normalized_visits_by_state_scaling.
"""

import pyarrow.parquet as pq
import numpy as np

file_path = '/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national_with_normalized/partisan_lean_2023-06.parquet'

print("Loading data...")
df = pq.read_table(file_path).to_pandas()

print("=== pct_visitors_matched distribution ===")
print(f"Total rows: {len(df):,}")
print(f"\nPercentiles:")
for p in [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]:
    val = np.nanpercentile(df['pct_visitors_matched'], p)
    print(f"  {p:3d}%: {val:.3f}")

print(f"\nNull count: {df['pct_visitors_matched'].isna().sum():,}")

print("\n=== Data retention at pct_visitors_matched thresholds ===")
for thresh in [0.5, 0.75, 0.90, 0.95, 0.99]:
    kept = (df['pct_visitors_matched'] >= thresh).sum()
    pct = kept / len(df) * 100
    print(f"  >= {thresh:.0%}: {kept:,} rows ({pct:.1f}%)")

print("\n=== normalized_visits_by_state_scaling distribution ===")
print(f"\nPercentiles:")
for p in [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]:
    val = np.nanpercentile(df['normalized_visits_by_state_scaling'], p)
    print(f"  {p:3d}%: {val:,.1f}")

print(f"\nNull count: {df['normalized_visits_by_state_scaling'].isna().sum():,}")
print(f"Zero count: {(df['normalized_visits_by_state_scaling'] == 0).sum():,}")

print("\n=== Brand-month total normalized_visits (for branded POIs) ===")
branded = df[df['brand'].notna()].copy()
brand_totals = branded.groupby('brand')['normalized_visits_by_state_scaling'].sum()
print(f"N brands in this month: {len(brand_totals):,}")
print(f"\nPercentiles of brand-month total visits:")
for p in [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]:
    val = np.nanpercentile(brand_totals, p)
    print(f"  {p:3d}%: {val:,.0f}")

print("\n=== Summary stats for brand-month totals ===")
print(f"Mean: {brand_totals.mean():,.0f}")
print(f"Median: {brand_totals.median():,.0f}")
print(f"Std: {brand_totals.std():,.0f}")

print("\nDone.")
