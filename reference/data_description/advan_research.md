# Advan Research Data Documentation

Source: https://docs.deweydata.io/docs/advan-research-weekly-patterns

## Overview

Advan Research provides foot traffic insights through mobile device panel data, tracking visits to points of interest (POIs) across the United States.

## Available Datasets

### Weekly Patterns
- **Refresh Cadence**: Monthly
- **Historical Coverage**: 2018-present
- **Geographic Scope**: United States
- **Observation Level**: Visits per week by POI
- **Release**: Three days after week end (Wednesdays)

### Monthly Patterns
- **Refresh Cadence**: Monthly
- **Historical Coverage**: 2019-present
- **Geographic Scope**: United States
- **Observation Level**: Visits per month by POI

## Core Methodology

### Visit Attribution
- Calculates visits using POI geometry (no dwell time filtering)
- Validated against publicly traded company revenue and credit card transactions
- Data suppression: <2 visitors = no reporting; 2-4 visitors reported as 4

### Home Location Determination
- Identifies home/work by analyzing most frequented buildings
- Uses calendar month windows
- Nighttime defined as 6pm-8am

### Panel Structure
- **Visitation Panel**: Consistent panel for year-over-year growth calculations
- **Trade Area Panel**: Broader panel with explicit permissions for geographic/demographic breakdowns
- Trade area values should be interpreted as ratios, not absolute numbers

### Backfill Process
- New POIs added monthly (excluding August and December)
- Historical data generated retroactively for new POIs
- Includes 20,000+ Industrial locations

### POI Data Stability
- POIs static as of June 2023 following SafeGraph changes
- Traffic attribution follows June 2023 Placekey assignment

## Data Schema

### POI Identification
| Variable | Description |
|----------|-------------|
| PLACEKEY | Unique POI identifier |
| PARENT_PLACEKEY | Parent location identifier |
| SAFEGRAPH_BRAND_IDS | Brand identifiers |
| LOCATION_NAME | POI name |
| STORE_ID | Store identifier |

### Classification
| Variable | Description |
|----------|-------------|
| TOP_CATEGORY | Primary category |
| SUB_CATEGORY | Secondary category |
| NAICS_CODE | NAICS 2017 code |
| CATEGORY_TAGS | Additional tags |

### Location Details
| Variable | Description |
|----------|-------------|
| LATITUDE, LONGITUDE | Coordinates |
| STREET_ADDRESS | Street address |
| CITY, REGION, POSTAL_CODE | Location details |
| ISO_COUNTRY_CODE | Country code |

### Geographic Data
| Variable | Description |
|----------|-------------|
| GEOMETRY_TYPE | Geometry type |
| POLYGON_WKT | Well-known text polygon |
| POLYGON_CLASS | Polygon classification |
| WKT_AREA_SQ_METERS | Area in square meters |
| INCLUDES_PARKING_LOT | Parking lot flag |

### Visitation Metrics
| Variable | Description |
|----------|-------------|
| RAW_VISIT_COUNTS | Raw visit count |
| RAW_VISITOR_COUNTS | Raw visitor count |
| VISITS_BY_DAY | Daily visit breakdown |
| VISITS_BY_EACH_HOUR | Hourly visit breakdown |
| NORMALIZED_VISITS_BY_STATE_SCALING | State-normalized visits |
| NORMALIZED_VISITS_BY_REGION_NAICS_VISITS | Region/NAICS normalized |

### Trade Area Data
| Variable | Description |
|----------|-------------|
| POI_CBG | POI Census Block Group |
| VISITOR_HOME_CBGS | Visitor home CBGs (JSON) |
| VISITOR_DAYTIME_CBGS | Visitor daytime CBGs |
| DISTANCE_FROM_HOME | Distance metrics |
| MEDIAN_DWELL | Median dwell time |

## Known Issues

- **Distance from Home Bug**: `distance_from_home` null for all POIs since November 2023
- **National Parks**: Data generation stopped after December 2022
- **CBG Data**: Uses 2018 boundaries

## Normalization Guidance

Apply normalization using:
```
factor = normalized_visits_by_state_scaling / raw_visits
```

## Supporting Data Files

- Home Location Distributions by State/Census Block Group
- Number of Visits/Visitors by State
- Normalization Stats (regional and day-of-week breakdowns)
