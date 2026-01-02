# Project Westwood: Master Plan

## Overview

**Goal:** Generate estimates of partisan lean of business visitors (proxy for consumers) by combining foot traffic data with geographic voting patterns.

**Method:** Match Advan foot traffic data (visitor_home_cbgs) to CBG-level election results (2020 presidential) to calculate a visitor-weighted partisan lean score for each point of interest (POI).

**Key Metric:** `rep_lean` = Two-party Republican vote share (Trump / (Trump + Biden)) weighted by visitor origin CBGs.

---

## Ohio Pilot: Key Findings (2023 Data)

### Data Summary
- **2.9 million** POI-month observations
- **328,000** unique points of interest
- **12 months** of data (Jan-Dec 2023)
- **Mean Republican lean:** 52.4% (slightly right of center)

### 1. The Measure is Reliable (Temporal Consistency)

| Test | Result | Interpretation |
|------|--------|----------------|
| Monthly aggregate variation | 0.35 pts (51.6%-52.9%) | Essentially flat |
| Within-POI std dev (median) | 3.7 pts | Individual locations barely move |
| Brand adjacent-month correlation | 0.90 | Very high stability |
| Brand Jan-Dec correlation | 0.84 | Consistent across full year |
| Q1-Q4 correlation | 0.87 | Quarterly stability |

**Conclusion:** The measure is capturing a stable characteristic of locations, not monthly noise.

### 2. Geography Dominates Brand

| Level | Variance Explained |
|-------|-------------------|
| Between-brand | 8% |
| Within-brand (location) | 85% |

**Examples of within-brand spread:**
- McDonald's: 14% - 84% R across Ohio locations (70 pt range)
- Starbucks: 17% - 80% R (63 pt range)
- Walmart: 18% - 81% R (63 pt range)

**Conclusion:** A Starbucks in rural Ohio (80% R) has more Republican visitors than almost any Walmart. Location matters ~10x more than brand identity.

### 3. Notable Brand Differences (unconditional)

| Matchup | Gap |
|---------|-----|
| Whole Foods (40%) vs Kroger (54%) | 14 pts |
| Target (48%) vs Walmart (58%) | 10 pts |
| Chick-fil-A (51%) vs McDonald's (55%) | 4 pts |
| Starbucks (49%) vs Dunkin' (52%) | 3 pts |

### 4. Within-Neighborhood Variation

Even controlling for location (same H3 geographic cell), different businesses attract different visitors:

| City | Avg within-neighborhood range |
|------|------------------------------|
| Cleveland | 15.8 pts |
| Columbus | 18.7 pts |
| Cincinnati | 18.5 pts |
| Toledo | 19.0 pts |

**Variance decomposition within cities:**
- Between-neighborhood: 75-87%
- Within-neighborhood (business type): 13-25%

**Conclusion:** Geography is dominant, but business type explains 13-25% of variance *within* neighborhoods. There is real consumer sorting by partisanship beyond pure geography.

### 5. Validation: Same Brand, Same Neighborhood

When the same brand has multiple locations in the same neighborhood:
- Median difference: **2.5 pts**

This confirms the measure is consistent and not driven by noise.

---

## Key Insights for Research

### What this measure captures:
1. **Primarily geographic sorting** - Where a business is located determines most of its visitor partisan composition
2. **Some consumer sorting** - Within neighborhoods, ~15-25% of variance is explained by business type
3. **Stable over time** - This is a characteristic of locations, not monthly fluctuation

### What this measure does NOT capture:
1. Individual-level partisanship of visitors
2. Causal effects of partisanship on consumer behavior
3. Changes in partisan composition over time (would need multi-year data)

### Potential research applications:
1. **Brand positioning:** Which brands attract more polarized vs. mixed audiences?
2. **Geographic analysis:** How does consumer partisan sorting vary by urbanicity?
3. **Industry comparisons:** Which sectors show more/less partisan segregation?
4. **Firm-level analysis:** Do firms with more polarized visitors perform differently?

---

## Data Pipeline

### Completed Steps (Ohio Pilot)

1. **Unzip election data** (`01a_unzip_ohio_election.slurm`)
   - Source: `/global/scratch/users/maxkagan/election_results_geocoded/`
   - Method: RLCR (Main Method) at Block Group level

2. **Build CBG lookup** (`01b_build_cbg_lookup.slurm`, `build_cbg_lookup.py`)
   - Output: `cbg_partisan_lean_ohio.parquet`
   - 9,472 Ohio CBGs with `two_party_rep_share_2020`

3. **Filter Advan data** (`02a_filter_advan.slurm`, `filter_advan.py`)
   - Source: `/global/scratch/users/maxkagan/advan/monthly_patterns_foot_traffic/`
   - Filter: Ohio POIs only, 2023 months
   - Output: 12 monthly parquet files

4. **Parse visitor CBGs** (`02b_parse_visitor_cbgs.slurm`, `parse_visitor_cbgs.py`)
   - Match visitor_home_cbgs to election results
   - Calculate weighted `rep_lean` per POI-month
   - Output: `ohio_2023.parquet` (105 MB, 2.9M rows)

5. **Descriptive analysis** (`ohio_2023_analysis.Rmd`)
   - Comprehensive R Markdown report with 8 sections
   - Output: `ohio_2023_analysis.html`

### File Locations

```
/global/home/users/maxkagan/project_oakland/
├── master_plan.md                    # This document
├── 01_data_processing/
│   ├── python/                       # Processing scripts
│   ├── slurm/                        # SLURM job scripts
│   └── logs/                         # Job logs
├── 02_descriptive_analysis/
│   ├── rmd/ohio_2023_analysis.Rmd    # Main analysis
│   ├── output/ohio_2023_analysis.html
│   └── slurm/, logs/
└── references/

/global/scratch/users/maxkagan/project_oakland/
├── inputs/
│   ├── election_data_raw/            # Unzipped election CSVs
│   └── cbg_partisan_lean_ohio.parquet
├── intermediate/
│   └── advan_2023_filtered/          # Monthly parquet files
└── outputs/
    └── location_partisan_lean/ohio_2023.parquet
```

---

## Next Steps

### Immediate (Ohio)
- [ ] Collapse to POI-level annual averages
- [ ] Merge with business characteristics for regression analysis
- [ ] Explore within-category variation (e.g., fast food, grocery)

### Scale-Up (All States)
- [ ] Download/unzip election data for remaining 49 states
- [ ] Build national CBG lookup table
- [ ] Process Advan data by state (array jobs for large states)
- [ ] Combine into national dataset

### Analysis Extensions
- [ ] Urban/suburban/rural breakdown
- [ ] Time series analysis (2019-2024)
- [ ] Firm-level aggregation (parent company analysis)
- [ ] Comparison with other polarization measures

---

## Technical Notes

### CBG Matching
- Uses 12-digit FIPS codes from `visitor_home_cbgs` JSON field
- Matches to 2020 presidential election results at Block Group level
- Method: RLCR (regression-based disaggregation from precinct to CBG)

### Placekey Geographic Encoding
- Format: `what@where` where `where` is an H3 geohash
- First 7 characters of `where` component define neighborhood-level cells
- Used for within-neighborhood variation analysis

### Memory Requirements
- Ohio data (2.9M rows): ~200-400 MB in memory
- savio2 (64 GB) sufficient for single-state processing
- May need savio3_bigmem for national aggregation

---

*Last updated: 2025-12-31*
*Author: Max Kagan (with Claude Code assistance)*
