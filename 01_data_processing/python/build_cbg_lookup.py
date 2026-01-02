"""
Build CBG partisan lean lookup table from geocoded election results.

For Ohio pilot, uses Main Method (RLCR) 2020 Block Group data.
Calculates two_party_rep_share_2020 = Trump / (Trump + Biden)

Usage:
    python build_cbg_lookup.py --state OH --output /path/to/output.parquet
"""

import argparse
import pandas as pd
from pathlib import Path


def build_cbg_lookup(input_file: Path, output_file: Path) -> pd.DataFrame:
    """
    Read CBG-level election data and create partisan lean lookup table.

    Args:
        input_file: Path to bg-2020-RLCR.csv
        output_file: Path for output parquet file

    Returns:
        DataFrame with CBG partisan lean data
    """
    print(f"Reading election data from: {input_file}")

    # Read the CSV
    df = pd.read_csv(input_file, dtype={'bg_GEOID': str})

    print(f"Loaded {len(df):,} CBGs")

    # Extract relevant columns
    # G20PRERTRU = Trump 2020
    # G20PREDBID = Biden 2020
    lookup = pd.DataFrame({
        'cbg_geoid': df['bg_GEOID'].astype(str).str.zfill(12),  # Ensure 12-digit format
        'trump_2020': df['G20PRERTRU'],
        'biden_2020': df['G20PREDBID'],
        'population': df['bg_population'],
    })

    # Calculate two-party Republican share
    total_two_party = lookup['trump_2020'] + lookup['biden_2020']
    lookup['two_party_rep_share_2020'] = lookup['trump_2020'] / total_two_party

    # Handle edge cases (CBGs with zero votes)
    lookup['two_party_rep_share_2020'] = lookup['two_party_rep_share_2020'].fillna(0.5)

    # Summary statistics
    print(f"\nSummary statistics:")
    print(f"  Total CBGs: {len(lookup):,}")
    print(f"  CBGs with votes: {(total_two_party > 0).sum():,}")
    print(f"  Mean Rep share: {lookup['two_party_rep_share_2020'].mean():.3f}")
    print(f"  Median Rep share: {lookup['two_party_rep_share_2020'].median():.3f}")
    print(f"  Std Dev: {lookup['two_party_rep_share_2020'].std():.3f}")

    # Save to parquet
    print(f"\nSaving to: {output_file}")
    lookup.to_parquet(output_file, index=False)

    print("Done!")
    return lookup


def main():
    parser = argparse.ArgumentParser(description="Build CBG partisan lean lookup table")
    parser.add_argument("--state", default="OH", help="State abbreviation (default: OH)")
    parser.add_argument("--input-dir",
                        default="/global/scratch/users/maxkagan/project_oakland/inputs/election_data_raw",
                        help="Directory containing extracted election data")
    parser.add_argument("--output",
                        default="/global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_ohio.parquet",
                        help="Output parquet file path")

    args = parser.parse_args()

    # Build input path based on state
    # Ohio FIPS = 39, so directory is "390 OH"
    state_fips = {"OH": "39"}
    fips = state_fips.get(args.state, "39")

    input_file = Path(args.input_dir) / f"{fips}0 {args.state}" / "Main Method" / "Block Groups" / "bg-2020-RLCR.csv"
    output_file = Path(args.output)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    build_cbg_lookup(input_file, output_file)


if __name__ == "__main__":
    main()
