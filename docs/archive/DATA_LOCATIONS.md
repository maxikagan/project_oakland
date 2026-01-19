# Data Locations Reference

## Primary Outputs (Use These)

| Data | Location | Size | Description |
|------|----------|------|-------------|
| **Partisan Lean** | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national/` | 29GB (79 files) | Monthly POI-level partisan lean (2019-01 to 2025-07) |
| **Neighborhood Patterns** | `/global/scratch/users/maxkagan/01_foot_traffic_location/advan_neighborhood_patterns/neighborhood-patterns/` | 148GB (807 files) | Advan neighborhood patterns (for gravity model baseline) |

## Input Data

| Data | Location | Description |
|------|----------|-------------|
| **CBG Election Data** | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/inputs/cbg_partisan_lean_national_both_years.parquet` | 2016 + 2020 CBG-level partisan lean |
| **CBSA Crosswalk** | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/inputs/cbsa_crosswalk.parquet` | CBG → MSA mapping |
| **Advan Monthly Patterns** | `/global/scratch/users/maxkagan/advan/monthly_patterns_foot_traffic/dewey_2024_08_27_parquet/` | Raw Advan foot traffic (177GB) |

## Intermediate Data

| Data | Location | Description |
|------|----------|-------------|
| **Filtered Advan** | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/intermediate/advan_filtered/` | State-filtered Advan data |
| **Per-file Partisan** | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/intermediate/partisan_lean_by_file/` | Per-source-file partisan lean |

## External Data (For Future Steps)

| Data | Location | Description |
|------|----------|-------------|
| **PAW Employers** | `/global/scratch/users/maxkagan/04_labor_workforce/revelio_20250416/company_crosswalk/company_crosswalk.parquet` | Politics at Work employer crosswalk (3GB) |
| **Election Results (Raw)** | `/global/scratch/users/maxkagan/02_election_voter/election_results_geocoded/` | Raw geocoded election data |

## Output Schema (Partisan Lean Files)

```
brand                   string   - Brand name (may be null)
city                    string   - City
date_range_start        datetime - Month start date
median_dwell            float    - Median dwell time (minutes)
naics_code              string   - 6-digit NAICS
parent_placekey         string   - Parent location identifier
placekey                string   - Unique POI identifier
poi_cbg                 string   - CBG where POI is located
raw_visitor_counts      float    - Raw visitor count
region                  string   - State abbreviation
sub_category            string   - Advan sub-category
top_category            string   - Advan top category
cbsa_title              string   - MSA name
rep_lean_2020           float    - Republican lean (2020 election)
rep_lean_2016           float    - Republican lean (2016 election)
total_visitors          int      - Total visitors with CBG data
matched_visitors        int      - Visitors matched to election data
pct_visitors_matched    float    - Match rate (0-1)
year                    int      - Year
month                   int      - Month
year_month              string   - YYYY-MM format
```

## Scripts Location

All scripts: `/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/`
