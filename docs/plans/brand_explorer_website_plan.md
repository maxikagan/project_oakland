# Brand Partisan Lean Explorer - Website Plan

**Goal**: Interactive Vercel-hosted website to explore national brand partisan lean data
**Pattern**: politicsatwork.org / whatisstrategy.org (Next.js, polished modern design)
**Status**: Planning → Ready to build
**Last updated**: 2026-01-20

---

## Interview Summary (2026-01-20)

### Audience & Purpose
- **Primary audience**: Academic researchers
- **Primary goal**: Explore & discover (not lookup or extraction)
- **Timeline**: Launch before paper as a teaser to generate interest
- **Access**: Password-protected (single shared password) for 2-5 trusted colleagues initially

### Key Decisions
| Question | Decision |
|----------|----------|
| Data transparency | Show all brands with caveats for low-confidence data |
| Downloads | Request-based ("Contact for data access") |
| Methodology depth | High-level summary, link to paper for details |
| Validation results | Save for paper - don't show on site yet |
| Mobile support | Basic (usable but optimized for desktop) |
| Visual style | Polished & modern (like politicsatwork.org) |
| Categories | NAICS hierarchy (2-digit → 4-digit → 6-digit) |
| Map technology | Best technical choice (no preference) |
| Site name | Tied to paper title (working title for now) |
| Domain | Vercel subdomain initially (e.g., brand-lean.vercel.app) |
| MVP scope | Full featured from start |

### Feature Specifications
| Feature | Specification |
|---------|---------------|
| Landing page | Featured household name brands (McDonald's, Walmart, Starbucks, etc.) |
| Map views | Toggle between: absolute lean, relative to local area, relative to brand average |
| Time series | User-selectable: quarterly default, option for monthly granularity |
| Brand comparison | All modes: side-by-side, overlay on same chart, category benchmarking |

---

## Context: Existing Dashboard

An earlier Streamlit prototype exists at `dashboard/`:
- **Neighbor Map** (1_neighbor_map.py) - POIs colored by excess partisan lean
- **Brand Explorer** (2_brand_explorer.py) - Search/compare brands
- **MSA Analysis** (3_msa_analysis.py) - MSA-level exploration

**Limitations of Streamlit approach**:
- Requires SSH tunnel to Savio - not publicly accessible
- Python/Streamlit less performant than React for large datasets
- Not suitable for sharing with colleagues

**This Next.js site will supplant the Streamlit dashboard** with a password-protected, production-quality explorer.

---

## Overview

An interactive data exploration platform for academic researchers to explore partisan lean of ~3,500 national brands across 79 months (2019-2025). Built with Next.js, deployed on Vercel with password protection.

### Data Sources

| Dataset | Rows | Description |
|---------|------|-------------|
| Brand × Month | 273K | Aggregated partisan lean by brand and month |
| POI × Month (national brands only) | ~120M | Individual store locations with partisan lean |
| POI Coordinates | ~10M | Lat/long lookup table (being extracted - Job 31706171) |

---

## Core Features

### 1. Landing Page with Featured Brands

**Description**: Showcase household name brands to immediately demonstrate value.

**Components**:
- Key statistics (# brands, # POIs, date range)
- Grid of ~12 featured household names with their partisan lean
- Quick links to search, map, rankings
- Password gate on first visit

**Featured brands** (examples): McDonald's, Walmart, Starbucks, Target, Chick-fil-A, Whole Foods, Home Depot, Costco, etc.

### 2. Brand Search & Profile

**Description**: Search for any national brand, view its partisan lean profile.

**Components**:
- Autocomplete search bar (fuzzy matching on brand name)
- Brand profile page showing:
  - Overall partisan lean (weighted average across all months)
  - Partisan lean vs. category benchmark
  - Time series chart with **user-selectable granularity** (quarterly default, monthly option)
  - Company metadata (parent company, ticker, NAICS, # of locations)
  - Distribution histogram (lean across all POIs)
  - **Data quality caveat** if limited locations or time coverage

### 3. Interactive POI Map

**Description**: Map showing individual store locations with multiple view modes.

**View Modes** (toggle between):
1. **Absolute lean**: Raw partisan lean score (0-1 scale), red↔blue gradient
2. **Relative to local area**: Excess lean compared to surrounding geography
3. **Relative to brand average**: How each store compares to brand's national average

**Filters**:
- Filter by brand (single or multiple)
- Filter by MSA
- Combined filters (e.g., "Starbucks in San Francisco MSA")

**Interactions**:
- Click POI for popup with details
- Cluster markers when zoomed out
- Smooth pan/zoom

### 4. MSA Geographic Analysis

**Description**: Choropleth map of MSAs with drill-down capability.

**Components**:
- US map with MSA boundaries colored by aggregate lean
- Color by: overall lean, category lean, or specific brand
- Click MSA → See top brands in that MSA
- MSA comparison (side-by-side)

### 5. Category Explorer

**Description**: Browse brands by NAICS hierarchy.

**Structure**: NAICS 2-digit → 4-digit → 6-digit → brands

**Components**:
- Hierarchical navigation
- Category summary stats (mean lean, std dev, # brands)
- Ranked list of brands within category

### 6. Rankings & Leaderboards

**Description**: Quick access to extreme brands.

**Views**:
- Top 50 most Republican brands
- Top 50 most Democratic brands
- Biggest movers (most temporal change)
- Most polarized (highest within-brand variance)

**Filters**: Category, minimum locations

### 7. Brand Comparison Tool

**Description**: Compare multiple brands directly.

**Modes**:
- Side-by-side profiles (2-3 brands)
- Overlay on same time series chart
- Category benchmarking (brand vs. category average)

### 8. Methodology

**Description**: High-level explanation with link to paper.

**Content**:
- 1-2 paragraph overview of data sources and approach
- Conceptual explanation (not formulas)
- Link to paper for technical details (when available)
- Known limitations

### 9. Data Access

**Description**: Request-based data access.

**Content**:
- "Contact for data access" with email link
- Brief description of what's available
- Note about forthcoming paper

---

## Technical Architecture

### Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | Next.js 14 (App Router) | SSR, React Server Components, same as reference sites |
| Hosting | Vercel (free tier) | Automatic deploys, edge functions, subdomain |
| Styling | Tailwind CSS | Rapid prototyping, responsive design |
| Maps | Mapbox GL JS or Deck.gl | WebGL-accelerated, handles many points |
| Charts | Recharts or D3.js | Time series, histograms, bar charts |
| Data | Static JSON + API routes | Pre-aggregated data files, on-demand filtering |
| Search | Fuse.js (client-side) | Fuzzy search for brand names |
| Auth | Simple password gate | Single shared password, stored in env var |

### Password Protection

Simple client-side password gate:
- Password stored in Vercel environment variable
- Cookie/localStorage to remember authenticated sessions
- No user accounts needed for 2-5 person access

### Data Strategy

**Multi-tier architecture**:

1. **Static JSON (build-time)**:
   - Brand metadata + overall lean (~500KB)
   - Brand monthly time series (~5MB)
   - MSA summaries (~2MB)
   - Category summaries (~100KB)
   - Featured brands list (~10KB)

2. **API Routes (on-demand)**:
   - POI data for specific brand + MSA combinations
   - Paginated results, max 10K POIs per request

3. **Map Data**:
   - Start with dynamic loading (API returns POIs → render)
   - Migrate to vector tiles if performance is an issue

---

## Page Structure

```
/                           # Landing page (password gate) + featured brands
/brand/[slug]               # Brand profile page
/map                        # Interactive POI map
/map?brand=starbucks        # Map filtered to brand
/map?msa=san-francisco      # Map filtered to MSA
/msa                        # MSA explorer (choropleth)
/msa/[slug]                 # Individual MSA profile
/categories                 # NAICS hierarchy browser
/categories/[naics]         # Category detail
/rankings                   # Top Republican/Democratic brands
/compare                    # Brand comparison tool
/methodology                # High-level methods
/data                       # "Contact for access" page
```

---

## Data Preparation Tasks

### Task A: POI Coordinates (IN PROGRESS)
- **Job**: 31706171 (running)
- **Source**: Raw Advan CSV.gz files
- **Output**: `outputs/poi_coordinates.parquet` (placekey → lat, lon)

### Task B: Join Coordinates to Partisan Lean
- **Source**: `outputs/national_with_normalized/*.parquet` + coordinates
- **Output**: Updated parquet files with latitude, longitude columns

### Task C: Brand Summary JSON
- **Source**: `brand_month_partisan_lean.parquet`
- **Output**: `brands.json` with metadata + overall lean

### Task D: Brand Time Series JSON
- **Source**: `brand_month_partisan_lean.parquet`
- **Output**: Single JSON or per-brand files for time series

### Task E: MSA Summary JSON
- **Source**: Aggregate from POI data by MSA
- **Output**: `msa_summaries.json`

### Task F: Category Summaries
- **Source**: Aggregate brand data by NAICS
- **Output**: `categories.json` with NAICS hierarchy

### Task G: Featured Brands List
- **Source**: Manual curation of household names
- **Output**: `featured_brands.json`

### Task H: POI Data for API
- **Source**: POI-level data with coordinates
- **Output**: Partitioned files for API access (by brand or MSA)

---

## Development Approach

Since **full featured from start** is the goal, build all features in one phase rather than staged MVP:

### Implementation Order

1. **Infrastructure**
   - Next.js project setup with Tailwind
   - Password gate component
   - Data loading utilities
   - Deploy to Vercel subdomain

2. **Core Pages**
   - Landing page with featured brands
   - Brand profile with time series chart
   - Rankings page

3. **Search & Navigation**
   - Brand search with autocomplete
   - Category browser (NAICS hierarchy)

4. **Maps**
   - POI map with three view modes
   - Brand/MSA filter controls
   - MSA choropleth

5. **Comparison & Analysis**
   - Brand comparison tool
   - MSA profiles and comparison

6. **Content Pages**
   - Methodology
   - Data access request

7. **Polish**
   - Mobile responsiveness (basic)
   - Loading states
   - Error handling

---

## Repository Structure

```
brand-explorer/
├── app/
│   ├── page.tsx              # Landing + password gate
│   ├── brand/[slug]/page.tsx # Brand profile
│   ├── map/page.tsx          # Interactive map
│   ├── msa/page.tsx          # MSA explorer
│   ├── msa/[slug]/page.tsx   # MSA profile
│   ├── categories/page.tsx   # NAICS browser
│   ├── rankings/page.tsx     # Leaderboards
│   ├── compare/page.tsx      # Comparison tool
│   ├── methodology/page.tsx  # Methods
│   └── data/page.tsx         # Data access
├── components/
│   ├── PasswordGate.tsx
│   ├── BrandSearch.tsx
│   ├── TimeSeriesChart.tsx
│   ├── POIMap.tsx
│   ├── MSAChoropleth.tsx
│   ├── BrandCard.tsx
│   └── ...
├── lib/
│   ├── data.ts               # Data loading
│   ├── brands.ts             # Brand utilities
│   └── maps.ts               # Map utilities
├── data/                     # Static JSON (git-tracked)
├── public/                   # Static assets
└── api/                      # API routes for POI data
```

---

## Dependencies on Research Pipeline

| Website Feature | Depends On | Status |
|-----------------|------------|--------|
| Brand profiles | brand_month_partisan_lean.parquet | ✅ Ready |
| POI map | POI coordinates | 🔄 Job 31706171 running |
| MSA analysis | POI → MSA mapping | ✅ Ready |
| Category explorer | NAICS codes in brand data | ✅ Ready |

---

## Open Items

1. **Site name**: Defer until paper title is finalized (use working title)
2. **Password**: Choose a memorable shared password
3. **Featured brands**: Curate list of ~12 household names
4. **Coordinate extraction**: Wait for Job 31706171 to complete

---

*See also: RESEARCH_PLAN.md Epic 3 Phase 2*
