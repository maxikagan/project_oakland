"""
Filter Advan monthly patterns data to all US states in a single pass.

Reads each monthly file once and outputs filtered data for each state.
More efficient than processing state-by-state which would re-read the same file.

Usage:
    python filter_advan_all_states.py --month 2023-01-01
"""

import argparse
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path
import json
import sys

COLUMNS_TO_KEEP = [
    'PLACEKEY',
    'PARENT_PLACEKEY',
    'SAFEGRAPH_BRAND_IDS',
    'LOCATION_NAME',
    'BRANDS',
    'STORE_ID',
    'TOP_CATEGORY',
    'SUB_CATEGORY',
    'NAICS_CODE',
    'LATITUDE',
    'LONGITUDE',
    'STREET_ADDRESS',
    'CITY',
    'REGION',
    'POSTAL_CODE',
    'OPENED_ON',
    'CLOSED_ON',
    'TRACKING_CLOSED_SINCE',
    'WEBSITES',
    'GEOMETRY_TYPE',
    'POLYGON_CLASS',
    'ENCLOSED',
    'IS_SYNTHETIC',
    'ISO_COUNTRY_CODE',
    'DATE_RANGE_END',
    'RAW_VISIT_COUNTS',
    'RAW_VISITOR_COUNTS',
    'POI_CBG',
    'VISITOR_HOME_CBGS',
    'VISITOR_HOME_AGGREGATION',
    'VISITOR_DAYTIME_CBGS',
    'DISTANCE_FROM_HOME',
    'MEDIAN_DWELL',
    'BUCKETED_DWELL_TIMES',
    'RELATED_SAME_DAY_BRAND',
    'RELATED_SAME_MONTH_BRAND',
    'NORMALIZED_VISITS_BY_STATE_SCALING',
    'NORMALIZED_VISITS_BY_REGION_NAICS_VISITS',
    'NORMALIZED_VISITS_BY_REGION_NAICS_VISITORS',
    'NORMALIZED_VISITS_BY_TOTAL_VISITS',
    'NORMALIZED_VISITS_BY_TOTAL_VISITORS',
]

US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
    'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
    'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
    'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
    'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]


def filter_all_states(input_file: Path, output_dir: Path, month: str) -> dict:
    """
    Read Advan parquet file once and filter to all US states.

    Args:
        input_file: Path to Advan parquet file
        output_dir: Directory for output parquet files
        month: Month string for naming (e.g., "2023-01-01")

    Returns:
        Dictionary with processing statistics
    """
    print(f"Reading: {input_file}")
    print(f"File size: {input_file.stat().st_size / 1e9:.2f} GB")

    parquet_file = pq.ParquetFile(input_file)
    total_rows = parquet_file.metadata.num_rows
    print(f"Total rows in file: {total_rows:,}")

    filters = [('ISO_COUNTRY_CODE', '=', 'US')]

    print(f"Loading US data with {len(COLUMNS_TO_KEEP)} columns...")
    table = pq.read_table(
        input_file,
        columns=COLUMNS_TO_KEEP,
        filters=filters
    )

    us_rows = table.num_rows
    print(f"US rows loaded: {us_rows:,}")

    region_array = table.column('REGION')

    stats = {
        'month': month,
        'input_file': str(input_file),
        'total_rows': total_rows,
        'us_rows': us_rows,
        'states': {}
    }

    parquet_dir = output_dir / "parquet"
    parquet_dir.mkdir(parents=True, exist_ok=True)

    for state in US_STATES:
        mask = pa.compute.equal(region_array, state)
        state_table = table.filter(mask)
        state_rows = state_table.num_rows

        if state_rows > 0:
            output_file = parquet_dir / f"{state}_{month}.parquet"
            pq.write_table(state_table, output_file)
            output_size_mb = output_file.stat().st_size / 1e6

            stats['states'][state] = {
                'rows': state_rows,
                'size_mb': round(output_size_mb, 1)
            }
            print(f"  {state}: {state_rows:,} POIs ({output_size_mb:.1f} MB)")
        else:
            stats['states'][state] = {'rows': 0, 'size_mb': 0}

    total_state_rows = sum(s['rows'] for s in stats['states'].values())
    print(f"\nTotal rows written: {total_state_rows:,}")
    print(f"States with data: {sum(1 for s in stats['states'].values() if s['rows'] > 0)}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Filter Advan data to all US states")
    parser.add_argument("--month", required=True, help="Month to process (e.g., 2023-01-01)")
    parser.add_argument("--input-dir",
                        default="/global/scratch/users/maxkagan/advan/monthly_patterns_foot_traffic/dewey_2024_08_27_parquet",
                        help="Advan parquet directory")
    parser.add_argument("--output-dir",
                        default="/global/scratch/users/maxkagan/project_oakland/intermediate/advan_national_filtered",
                        help="Output directory")

    args = parser.parse_args()

    input_file = Path(args.input_dir) / f"DATE_RANGE_START={args.month}" / "part-0.parquet"
    output_dir = Path(args.output_dir)

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    stats = filter_all_states(input_file, output_dir, args.month)

    stats_dir = output_dir / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    stats_file = stats_dir / f"{args.month}_stats.json"

    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\nStats saved to: {stats_file}")


if __name__ == "__main__":
    main()
