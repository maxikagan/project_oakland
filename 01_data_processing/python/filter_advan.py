"""
Filter Advan monthly patterns data to a specific state.

Uses pyarrow's row-level filtering and column selection to minimize memory usage.

Usage:
    python filter_advan.py --state OH --month 2023-01-01 --output-dir /path/to/output/
"""

import argparse
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa
from pathlib import Path
import json

# Columns to keep (41 of 52) - drops POLYGON_WKT, OPEN_HOURS, CATEGORY_TAGS, etc.
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


def filter_advan_month(input_file: Path, output_file: Path, state: str = "OH") -> dict:
    """
    Read Advan parquet file with filtering, extract state data, and save.

    Uses pyarrow's built-in filtering to avoid loading entire file.

    Args:
        input_file: Path to Advan parquet file
        output_file: Path for output parquet file
        state: State abbreviation to filter (default: OH)

    Returns:
        Dictionary with processing statistics
    """
    print(f"Reading: {input_file}")
    print(f"File size: {input_file.stat().st_size / 1e9:.2f} GB")

    # Read parquet metadata first
    parquet_file = pq.ParquetFile(input_file)
    total_rows = parquet_file.metadata.num_rows
    print(f"Total rows in file: {total_rows:,}")
    print(f"Columns: {parquet_file.schema.names[:10]}...")  # First 10 columns

    # Build filter expression
    # Filter: REGION == state AND ISO_COUNTRY_CODE == 'US'
    filters = [
        ('REGION', '=', state),
        ('ISO_COUNTRY_CODE', '=', 'US')
    ]

    print(f"Applying filters: REGION=={state}, ISO_COUNTRY_CODE==US")
    print(f"Selecting {len(COLUMNS_TO_KEEP)} of 52 columns (dropping POLYGON_WKT, etc.)")

    # Read with filtering AND column selection - minimizes memory usage
    table = pq.read_table(
        input_file,
        columns=COLUMNS_TO_KEEP,
        filters=filters
    )

    filtered_rows = table.num_rows
    print(f"Rows after filtering: {filtered_rows:,}")
    print(f"Reduction: {100*(1 - filtered_rows/total_rows):.1f}%")

    # Save filtered data
    print(f"Saving to: {output_file}")
    pq.write_table(table, output_file)

    # Get output file size
    output_size = output_file.stat().st_size / 1e6
    print(f"Output file size: {output_size:.1f} MB")

    stats = {
        'input_file': str(input_file),
        'total_rows': total_rows,
        'filtered_rows': filtered_rows,
        'state': state,
        'output_size_mb': output_size,
        'columns_kept': len(COLUMNS_TO_KEEP),
        'columns_total': len(parquet_file.schema.names),
        'columns': COLUMNS_TO_KEEP
    }

    print(f"Done! Kept {filtered_rows:,} of {total_rows:,} rows ({100*filtered_rows/total_rows:.2f}%)")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Filter Advan data to state")
    parser.add_argument("--state", default="OH", help="State abbreviation (default: OH)")
    parser.add_argument("--month", required=True, help="Month to process (e.g., 2023-01-01)")
    parser.add_argument("--input-dir",
                        default="/global/scratch/users/maxkagan/advan/monthly_patterns_foot_traffic/dewey_2024_08_27_parquet",
                        help="Advan parquet directory")
    parser.add_argument("--output-dir",
                        default="/global/scratch/users/maxkagan/project_oakland/intermediate/advan_2023_filtered",
                        help="Output directory")

    args = parser.parse_args()

    # Build paths
    input_file = Path(args.input_dir) / f"DATE_RANGE_START={args.month}" / "part-0.parquet"
    output_dir = Path(args.output_dir)

    # Create parquet and stats subdirectories
    parquet_dir = output_dir / "parquet"
    stats_dir = output_dir / "stats"
    parquet_dir.mkdir(parents=True, exist_ok=True)
    stats_dir.mkdir(parents=True, exist_ok=True)

    output_file = parquet_dir / f"{args.state}_{args.month}.parquet"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    stats = filter_advan_month(input_file, output_file, args.state)

    # Save stats
    stats_file = stats_dir / f"{args.state}_{args.month}_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"Stats saved to: {stats_file}")


if __name__ == "__main__":
    main()
