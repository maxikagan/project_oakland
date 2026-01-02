# Politics at Work (VRscores) Data Documentation

Source: https://politicsatwork.org/download-data

## Overview

VRscores provides partisan composition data for U.S. employers and other aggregation levels, derived from L2 voter registration records matched to employment data.

## Available Datasets

All datasets span 2012-2024 and are available in Parquet or CSV formats via Harvard Dataverse.

### 1. Employer-Year Panel (VRID x Year)
- **Observations**: 6.26M employer-year records
- **Unique Employers**: 534K+
- **Minimum Threshold**: 5 unique workers per employer

### 2. Occupation-Year Panel (SOC x Year)
- **Observations**: 4,979 occupation-year rows
- **Coverage**: 256 6-digit SOC groups

### 3. Industry-Year Panel (NAICS x Year)
- **Observations**: 13,131 NAICS 6-digit industry rows
- **Coverage**: ~1,010 industries per year

### 4. MSA-Year Panel (Metro x Year)
- **Observations**: 4,758 metro-year records
- **Coverage**: 366 Metropolitan Statistical Areas

## Variable Definitions

### Identifier & Metadata
| Variable | Description |
|----------|-------------|
| `vrid` | Stable employer identifier across years |
| `company_name` | Employer name |
| `year` | Calendar year |
| `latest_processed_at` | ISO 8601 timestamp of last processing |

### Worker Counts
| Variable | Description |
|----------|-------------|
| `employee_count` | Unique workers (minimum 5) |
| `dem_workers_raw` | Raw Democratic worker count |
| `rep_workers_raw` | Raw Republican worker count |
| `other_workers_raw` | Raw other/independent worker count |
| `dem_workers_imp` | Imputed Democratic worker count |
| `rep_workers_imp` | Imputed Republican worker count |
| `other_workers_imp` | Imputed other worker count |
| `avg_match_quality` | Probability of accurate worker matches |

### Partisan Composition Metrics
| Variable | Description |
|----------|-------------|
| `pct_dem_raw` | Raw Democratic percentage |
| `pct_rep_raw` | Raw Republican percentage |
| `pct_dem_imp` | Imputed Democratic percentage |
| `pct_rep_imp` | Imputed Republican percentage |
| `two_party_margin_raw` | Raw two-party margin (Dem - Rep) |
| `two_party_margin_imp` | Imputed two-party margin |
| `political_diversity_raw` | Herfindahl-based diversity (higher = more diverse) |
| `political_diversity_imp` | Imputed diversity measure |
| `effective_parties_raw` | Inverse Herfindahl index |
| `effective_parties_imp` | Imputed effective parties |

## Methodology Notes

### Data Source
- Based on L2 voter registration records
- Matched to employment/workplace data

### Imputation
- Addresses unmatched or unknown party affiliation records
- Raw metrics use only matched records
- Imputed metrics estimate partisanship for unknowns

### Thresholds
- Default: Excludes employers with fewer than 25 matched workers
- Minimum: 5 workers for inclusion in dataset

## Terms of Use

- **Noncommercial use only**
- No governmental/quasi-governmental applications
- No political activity applications

## Access

Datasets hosted on Harvard Dataverse. Can be accessed via:
- Direct download (Parquet or CSV)
- Programmatic access using DuckDB and Polars
- curl for file preview
