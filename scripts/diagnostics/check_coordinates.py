#!/usr/bin/env python3
"""Quick check for latitude/longitude in our data files."""

import pyarrow.parquet as pq
from pathlib import Path

print("=" * 60)
print("Checking for latitude/longitude in data files")
print("=" * 60)

# Check intermediate files
intermediate = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/intermediate/partisan_lean_by_file")
files = list(intermediate.glob("*.parquet"))[:1]
if files:
    print(f"\n1. Intermediate file ({files[0].name}):")
    schema = pq.read_schema(files[0])
    coord_cols = [f.name for f in schema if 'lat' in f.name.lower() or 'lon' in f.name.lower()]
    print(f"   Coordinate columns: {coord_cols if coord_cols else 'NONE'}")
    print(f"   All columns: {[f.name for f in schema]}")
else:
    print("\n1. No intermediate files found")

# Check national output
national = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national")
files = list(national.glob("partisan_lean_2023-01.parquet"))[:1]
if files:
    print(f"\n2. National output ({files[0].name}):")
    schema = pq.read_schema(files[0])
    coord_cols = [f.name for f in schema if 'lat' in f.name.lower() or 'lon' in f.name.lower()]
    print(f"   Coordinate columns: {coord_cols if coord_cols else 'NONE'}")
else:
    print("\n2. No national output found")

# Check national_with_normalized
normalized = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national_with_normalized")
files = list(normalized.glob("partisan_lean_2023-01.parquet"))[:1]
if files:
    print(f"\n3. National with normalized ({files[0].name}):")
    schema = pq.read_schema(files[0])
    coord_cols = [f.name for f in schema if 'lat' in f.name.lower() or 'lon' in f.name.lower()]
    print(f"   Coordinate columns: {coord_cols if coord_cols else 'NONE'}")
    print(f"   All columns: {[f.name for f in schema]}")
else:
    print("\n3. No national_with_normalized found")

print("\n" + "=" * 60)
print("Done")
