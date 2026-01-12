"""
Build national CBG partisan lean lookup table from geocoded election results.

Processes all states using Main Method (RLCR) 2020 Block Group data.
Calculates two_party_rep_share_2020 = Trump / (Trump + Biden)

Usage:
    python build_cbg_lookup_national.py
"""

import pandas as pd
from pathlib import Path
import sys


STATE_FIPS = {
    "AL": "01", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "DC": "11", "FL": "12", "GA": "13",
    "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20",
    "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25",
    "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
    "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35",
    "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40",
    "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51",
    "WA": "53", "WV": "54", "WI": "55", "WY": "56"
}

INPUT_DIR = Path("/global/scratch/users/maxkagan/project_oakland/inputs/election_data_raw")
OUTPUT_FILE = Path("/global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national.parquet")


def process_state(state_abbr: str, fips: str) -> pd.DataFrame:
    """Process a single state's CBG election data."""
    dir_name = f"{fips}0 {state_abbr}"
    input_file = INPUT_DIR / dir_name / "Main Method" / "Block Groups" / "bg-2020-RLCR.csv"

    if not input_file.exists():
        print(f"  WARNING: File not found for {state_abbr}: {input_file}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(input_file, dtype={'bg_GEOID': str})

        lookup = pd.DataFrame({
            'cbg_geoid': df['bg_GEOID'].astype(str).str.zfill(12),
            'state': state_abbr,
            'trump_2020': df['G20PRERTRU'],
            'biden_2020': df['G20PREDBID'],
            'population': df['bg_population'],
        })

        total_two_party = lookup['trump_2020'] + lookup['biden_2020']
        lookup['two_party_rep_share_2020'] = lookup['trump_2020'] / total_two_party
        lookup['two_party_rep_share_2020'] = lookup['two_party_rep_share_2020'].fillna(0.5)

        print(f"  {state_abbr}: {len(lookup):,} CBGs, mean R share: {lookup['two_party_rep_share_2020'].mean():.3f}")
        return lookup

    except Exception as e:
        print(f"  ERROR processing {state_abbr}: {e}")
        return pd.DataFrame()


def main():
    print("Building national CBG partisan lean lookup")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output file: {OUTPUT_FILE}")
    print("-" * 60)

    all_states = []
    missing_states = []

    for state_abbr, fips in sorted(STATE_FIPS.items()):
        result = process_state(state_abbr, fips)
        if len(result) > 0:
            all_states.append(result)
        else:
            missing_states.append(state_abbr)

    if not all_states:
        print("ERROR: No states processed successfully!")
        sys.exit(1)

    print("-" * 60)
    national = pd.concat(all_states, ignore_index=True)

    print(f"\nNational summary:")
    print(f"  Total CBGs: {len(national):,}")
    print(f"  States processed: {len(all_states)}")
    print(f"  Missing states: {missing_states}")
    print(f"  Mean Rep share: {national['two_party_rep_share_2020'].mean():.3f}")
    print(f"  Median Rep share: {national['two_party_rep_share_2020'].median():.3f}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    national.to_parquet(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
