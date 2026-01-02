# SafeGraph Data Documentation

Source: https://docs.deweydata.io/docs/safegraph

## Overview

SafeGraph provides detailed information about physical places with accurate geocodes, open dates, place types, and consumer behavior context.

## Available Datasets (via Dewey)

### 1. Global Places - POI Data
- **Description**: Detailed information about physical places
- **Key Features**: Accurate geocodes, open dates, place types, consumer behavior context
- **Primary Key**: `placekey`
- **Format**: Delimited CSVs
- **Update Frequency**: Monthly

### 2. Spend Patterns - Entire US
- **Description**: Anonymized debit and credit card transaction data aggregated to individual places
- **Geographic Scope**: United States

## Important Notes

**Patterns Data Discontinued**: SafeGraph stopped publishing Weekly, Monthly, and Neighborhood Patterns data at the end of 2022. Researchers using older Patterns data should cite Advan Research as the source instead.

## Use Case Applications

- GIS and spatial representation
- Location-based services and POI applications
- Market research and economic geography
- Urban planning and commercial landscapes
- Consumer economics and spending patterns

## Access Restrictions

Partner-specific terms prohibit:
- Targeted advertising based on visits to sensitive locations
- Financial services or investment applications
- Certain geographic restrictions (UK, Middle East, park visualizations)

## Transition to Advan Research

For foot traffic and visitation patterns data, use Advan Research datasets:
- Weekly Patterns
- Monthly Patterns
- Neighborhood Patterns

See `advan_research.md` for detailed documentation.
