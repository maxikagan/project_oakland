#!/usr/bin/env python3
"""
Export JSON files for the Brand Partisan Lean Explorer website.

Exports (not blocked on coordinates):
  - brands.json: Brand metadata + overall lean
  - brand_timeseries.json: Monthly time series for all brands
  - categories.json: NAICS hierarchy with summary stats
  - featured_brands.json: Curated list of household names

Usage:
    python3 export_website_json.py
"""

import pandas as pd
import json
from pathlib import Path
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
BRAND_MONTH_PATH = PROJECT_DIR / "outputs" / "brand_month_aggregated" / "brand_month_partisan_lean.parquet"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "website_data"

FEATURED_BRANDS = [
    ("McDonald's", "McDonald's"),
    ("Walmart", "Walmart"),
    ("Starbucks", "Starbucks"),
    ("Target", "Target"),
    ("Chick-fil-A", "Chick-fil-A"),
    ("Whole Foods", "Whole Foods"),
    ("The Home Depot", "Home Depot"),
    ("Costco", "Costco"),
    ("Lowe's", "Lowe's"),
    ("Walgreens", "Walgreens"),
    ("CVS", "CVS"),
    ("Kroger", "Kroger"),
]


def export_brand_summary(df: pd.DataFrame) -> dict:
    """Create brand summary with overall lean and metadata."""
    logger.info("Creating brand summary...")

    brand_summary = df.groupby('brand_name').agg(
        overall_lean_2020=('brand_lean_2020', 'mean'),
        overall_lean_2016=('brand_lean_2016', 'mean'),
        lean_std_2020=('brand_lean_2020', 'std'),
        total_visits=('total_normalized_visits', 'sum'),
        n_months=('year_month', 'nunique'),
        avg_pois=('n_pois', 'mean'),
        avg_states=('n_states', 'mean'),
        avg_cbsas=('n_cbsas', 'mean'),
        top_category=('top_category', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 and pd.notna(x.mode().iloc[0]) else None),
        naics_code=('naics_code', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 and pd.notna(x.mode().iloc[0]) else None),
        company_name=('company_name', 'first'),
        ticker=('ticker', 'first'),
        gvkey=('gvkey', 'first'),
    ).reset_index()

    brands_list = []
    for _, row in brand_summary.iterrows():
        brands_list.append({
            'name': row['brand_name'],
            'slug': row['brand_name'].lower().replace(' ', '-').replace("'", ''),
            'lean_2020': round(row['overall_lean_2020'], 4) if pd.notna(row['overall_lean_2020']) else None,
            'lean_2016': round(row['overall_lean_2016'], 4) if pd.notna(row['overall_lean_2016']) else None,
            'lean_std': round(row['lean_std_2020'], 4) if pd.notna(row['lean_std_2020']) else None,
            'total_visits': int(row['total_visits']) if pd.notna(row['total_visits']) else 0,
            'n_months': int(row['n_months']),
            'avg_locations': round(row['avg_pois'], 1) if pd.notna(row['avg_pois']) else None,
            'avg_states': round(row['avg_states'], 1) if pd.notna(row['avg_states']) else None,
            'category': row['top_category'],
            'naics': row['naics_code'],
            'company': row['company_name'],
            'ticker': row['ticker'] if pd.notna(row['ticker']) else None,
        })

    logger.info(f"  {len(brands_list)} brands")
    return {'brands': brands_list, 'count': len(brands_list)}


def export_brand_timeseries(df: pd.DataFrame) -> dict:
    """Create time series data for all brands."""
    logger.info("Creating brand time series...")

    timeseries = {}
    for brand_name, group in df.groupby('brand_name'):
        slug = brand_name.lower().replace(' ', '-').replace("'", '')
        series = []
        for _, row in group.sort_values('year_month').iterrows():
            series.append({
                'month': row['year_month'],
                'lean_2020': round(row['brand_lean_2020'], 4) if pd.notna(row['brand_lean_2020']) else None,
                'lean_2016': round(row['brand_lean_2016'], 4) if pd.notna(row['brand_lean_2016']) else None,
                'visits': int(row['total_normalized_visits']) if pd.notna(row['total_normalized_visits']) else 0,
                'n_pois': int(row['n_pois']) if pd.notna(row['n_pois']) else 0,
            })
        timeseries[slug] = series

    logger.info(f"  {len(timeseries)} brands with time series")
    return timeseries


def export_categories(df: pd.DataFrame) -> dict:
    """Create NAICS hierarchy with summary stats."""
    logger.info("Creating category summaries...")

    brand_summary = df.groupby(['brand_name', 'naics_code', 'top_category']).agg(
        overall_lean_2020=('brand_lean_2020', 'mean'),
    ).reset_index()

    categories = {}

    for naics, group in brand_summary.groupby('naics_code'):
        if pd.isna(naics):
            continue

        naics_str = str(naics)
        naics_2 = naics_str[:2] if len(naics_str) >= 2 else naics_str
        naics_4 = naics_str[:4] if len(naics_str) >= 4 else naics_str

        if naics_2 not in categories:
            categories[naics_2] = {
                'code': naics_2,
                'level': 2,
                'subcategories': {},
                'brands': [],
                'stats': {}
            }

        if naics_4 not in categories[naics_2]['subcategories']:
            categories[naics_2]['subcategories'][naics_4] = {
                'code': naics_4,
                'level': 4,
                'brands': [],
                'stats': {}
            }

        for _, row in group.iterrows():
            brand_entry = {
                'name': row['brand_name'],
                'lean_2020': round(row['overall_lean_2020'], 4) if pd.notna(row['overall_lean_2020']) else None,
            }
            categories[naics_2]['subcategories'][naics_4]['brands'].append(brand_entry)
            categories[naics_2]['brands'].append(brand_entry)

    for naics_2, cat in categories.items():
        leans = [b['lean_2020'] for b in cat['brands'] if b['lean_2020'] is not None]
        if leans:
            cat['stats'] = {
                'n_brands': len(cat['brands']),
                'mean_lean': round(sum(leans) / len(leans), 4),
                'min_lean': round(min(leans), 4),
                'max_lean': round(max(leans), 4),
            }

        for naics_4, subcat in cat['subcategories'].items():
            sub_leans = [b['lean_2020'] for b in subcat['brands'] if b['lean_2020'] is not None]
            if sub_leans:
                subcat['stats'] = {
                    'n_brands': len(subcat['brands']),
                    'mean_lean': round(sum(sub_leans) / len(sub_leans), 4),
                }

    logger.info(f"  {len(categories)} NAICS 2-digit categories")
    return categories


def export_featured_brands(df: pd.DataFrame) -> list:
    """Create featured brands list with their data."""
    logger.info("Creating featured brands list...")

    brand_summary = df.groupby('brand_name').agg(
        overall_lean_2020=('brand_lean_2020', 'mean'),
        total_visits=('total_normalized_visits', 'sum'),
        avg_pois=('n_pois', 'mean'),
        top_category=('top_category', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 and pd.notna(x.mode().iloc[0]) else None),
    ).reset_index()

    featured = []
    for search_name, display_name in FEATURED_BRANDS:
        match = brand_summary[brand_summary['brand_name'].str.lower() == search_name.lower()]
        if len(match) == 0:
            match = brand_summary[brand_summary['brand_name'].str.lower().str.startswith(search_name.lower())]
        if len(match) == 0:
            match = brand_summary[brand_summary['brand_name'].str.contains(search_name, case=False, na=False, regex=False)]

        if len(match) > 0:
            row = match.iloc[0]
            featured.append({
                'name': display_name,
                'actual_name': row['brand_name'],
                'slug': display_name.lower().replace(' ', '-').replace("'", ''),
                'lean_2020': round(row['overall_lean_2020'], 4) if pd.notna(row['overall_lean_2020']) else None,
                'category': row['top_category'],
                'avg_locations': round(row['avg_pois'], 0) if pd.notna(row['avg_pois']) else None,
            })
            logger.info(f"  Found: {display_name} → {row['brand_name']} (lean: {row['overall_lean_2020']:.3f})")
        else:
            logger.warning(f"  NOT FOUND: {search_name}")

    logger.info(f"  {len(featured)} featured brands matched")
    return featured


def main():
    logger.info("=" * 60)
    logger.info("Exporting JSON files for website")
    logger.info("=" * 60)

    if not BRAND_MONTH_PATH.exists():
        logger.error(f"Brand month data not found: {BRAND_MONTH_PATH}")
        return 1

    logger.info(f"Loading {BRAND_MONTH_PATH}...")
    df = pd.read_parquet(BRAND_MONTH_PATH)
    logger.info(f"Loaded {len(df):,} brand-month rows")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    brands = export_brand_summary(df)
    with open(OUTPUT_DIR / 'brands.json', 'w') as f:
        json.dump(brands, f, indent=2)
    logger.info(f"Saved brands.json ({(OUTPUT_DIR / 'brands.json').stat().st_size / 1024:.1f} KB)")

    timeseries = export_brand_timeseries(df)
    with open(OUTPUT_DIR / 'brand_timeseries.json', 'w') as f:
        json.dump(timeseries, f)
    logger.info(f"Saved brand_timeseries.json ({(OUTPUT_DIR / 'brand_timeseries.json').stat().st_size / 1024 / 1024:.1f} MB)")

    categories = export_categories(df)
    with open(OUTPUT_DIR / 'categories.json', 'w') as f:
        json.dump(categories, f, indent=2)
    logger.info(f"Saved categories.json ({(OUTPUT_DIR / 'categories.json').stat().st_size / 1024:.1f} KB)")

    featured = export_featured_brands(df)
    with open(OUTPUT_DIR / 'featured_brands.json', 'w') as f:
        json.dump(featured, f, indent=2)
    logger.info(f"Saved featured_brands.json ({(OUTPUT_DIR / 'featured_brands.json').stat().st_size / 1024:.1f} KB)")

    logger.info("=" * 60)
    logger.info(f"All exports complete! Output: {OUTPUT_DIR}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
