#!/usr/bin/env python3
"""
Check population rates of HQ location fields in WRDS company crosswalk.
"""

import pyarrow.parquet as pq
import pyarrow.compute as pc

CROSSWALK_PATH = '/global/scratch/users/maxkagan/04_labor_workforce/revelio_20250416/crosswalks/company_crosswalk_wrds.parquet'

def main():
    print("Loading WRDS company crosswalk...")
    table = pq.read_table(CROSSWALK_PATH)
    total_rows = table.num_rows
    print(f"Total companies: {total_rows:,}\n")

    fields_to_check = [
        'hq_metro_area',
        'hq_city',
        'hq_state',
        'hq_country',
        'ticker',
        'gvkey',
        'cusip',
        'url',
        'naics_code'
    ]

    print("=" * 60)
    print(f"{'Field':<25} {'Populated':>12} {'Rate':>10}")
    print("=" * 60)

    for field in fields_to_check:
        if field in table.schema.names:
            col = table.column(field)
            non_null = pc.sum(pc.is_valid(col)).as_py()

            non_empty = non_null
            if col.type == 'string' or str(col.type) == 'string':
                non_empty_mask = pc.and_(
                    pc.is_valid(col),
                    pc.not_equal(col, '')
                )
                non_empty = pc.sum(non_empty_mask).as_py()

            rate = non_empty / total_rows * 100
            print(f"{field:<25} {non_empty:>12,} {rate:>9.1f}%")
        else:
            print(f"{field:<25} {'NOT FOUND':>12}")

    print("=" * 60)

    print("\n\nBreakdown by company size proxy (has ticker = likely larger):")
    has_ticker = pc.sum(pc.is_valid(table.column('ticker'))).as_py()
    no_ticker = total_rows - has_ticker

    print(f"  Companies with ticker: {has_ticker:,} ({has_ticker/total_rows*100:.1f}%)")
    print(f"  Companies without ticker: {no_ticker:,} ({no_ticker/total_rows*100:.1f}%)")

    ticker_mask = pc.is_valid(table.column('ticker'))
    with_ticker = table.filter(ticker_mask)
    without_ticker = table.filter(pc.invert(ticker_mask))

    print(f"\n  HQ metro populated among companies WITH ticker:")
    if 'hq_metro_area' in table.schema.names:
        hq_pop_with = pc.sum(pc.is_valid(with_ticker.column('hq_metro_area'))).as_py()
        print(f"    {hq_pop_with:,} / {with_ticker.num_rows:,} ({hq_pop_with/with_ticker.num_rows*100:.1f}%)")

    print(f"\n  HQ metro populated among companies WITHOUT ticker:")
    if 'hq_metro_area' in table.schema.names:
        hq_pop_without = pc.sum(pc.is_valid(without_ticker.column('hq_metro_area'))).as_py()
        print(f"    {hq_pop_without:,} / {without_ticker.num_rows:,} ({hq_pop_without/without_ticker.num_rows*100:.1f}%)")

if __name__ == '__main__':
    main()
