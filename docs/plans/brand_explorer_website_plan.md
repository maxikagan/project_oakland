# Brand Partisan Lean Explorer - Website Plan

**Goal**: Interactive Vercel-hosted website to explore national brand partisan lean data
**Pattern**: politicsatwork.org / whatisstrategy.org (Next.js, clean academic interface)
**Status**: Planning
**Last updated**: 2026-01-20

---

## Context: Existing Dashboard

An earlier Streamlit prototype exists at `dashboard/`:
- **Neighbor Map** (1_neighbor_map.py) - POIs colored by excess partisan lean
- **Brand Explorer** (2_brand_explorer.py) - Search/compare brands
- **MSA Analysis** (3_msa_analysis.py) - MSA-level exploration

**Limitations of Streamlit approach**:
- Requires SSH tunnel to Savio - not publicly accessible
- Python/Streamlit less performant than React for large datasets
- Not suitable for external dissemination

**This Next.js site will supplant the Streamlit dashboard** with a publicly accessible, production-quality explorer following the politicsatwork.org pattern.

---

## Overview

An interactive data exploration platform allowing researchers and the public to explore partisan lean of ~3,500 national brands across 79 months (2019-2025). Built with Next.js, deployed on Vercel.

### Data Sources

| Dataset | Rows | Description |
|---------|------|-------------|
| Brand × Month | 273K | Aggregated partisan lean by brand and month |
| POI × Month (national brands only) | ~120M | Individual store locations with partisan lean |
| POI Metadata | ~1.5M | Lat/long, MSA, NAICS, category for branded POIs |

---

## Core Features

### 1. Brand Search & Profile

**Description**: Search for any national brand, view its partisan lean profile.

**Components**:
- Autocomplete search bar (fuzzy matching on brand name)
- Brand profile page showing:
  - Overall partisan lean (weighted average across all months)
  - Partisan lean vs. category benchmark (e.g., "10% more Republican than Fast Food average")
  - Time series chart (monthly lean 2019-2025)
  - Company metadata (parent company, ticker, NAICS, # of locations)
  - Distribution histogram (lean across all POIs)

**Example**: Search "Chick-fil-A" → See it's more Republican than QSR average, stable over time, with map of locations.

### 2. Interactive POI Map

**Description**: Mapbox/Leaflet map showing individual store locations colored by partisan lean.

**Features**:
- **Filter by Brand**: Select one or more brands to display
- **Filter by MSA**: Zoom to or filter by metropolitan area
- **Filter by Both**: E.g., "Show all Starbucks in San Francisco MSA"
- **Color scale**: Red (Republican) ↔ Blue (Democratic) gradient
- **Click on POI**: Popup with store details, exact lean score, visitor count
- **Aggregation at zoom levels**: Cluster markers when zoomed out, individual POIs when zoomed in

**Use Cases**:
1. "How does Walmart's partisan lean vary across Texas?"
2. "Within the Columbus MSA, which coffee shops have the most Republican customers?"
3. "Compare Target vs Walmart locations in the same neighborhood"

### 3. MSA Geographic Analysis

**Description**: Choropleth map of MSAs colored by aggregate partisan lean, with drill-down.

**Components**:
- US map with MSA boundaries
- Color by: overall lean, lean for specific category, or lean for specific brand
- Click MSA → See top brands in that MSA, ranked by lean
- Compare MSAs side-by-side

### 4. Category Explorer

**Description**: Browse brands by NAICS code or top_category.

**Components**:
- Hierarchical browser (NAICS 2-digit → 4-digit → brands)
- Category summary stats (mean lean, std dev, # brands)
- Ranked list of brands within category
- Optional: Sunburst visualization (like politicsatwork.org)

### 5. Rankings & Leaderboards

**Description**: Quick access to most Republican / most Democratic brands.

**Components**:
- Top 50 most Republican brands (with filters: category, min locations)
- Top 50 most Democratic brands
- Biggest movers (brands whose lean changed most over time)
- Most polarized (highest variance across locations)

### 6. Methodology

**Description**: Documentation of data sources, methodology, limitations.

**Sections**:
- Data sources (Advan foot traffic, CBG election results)
- Aggregation methodology (weighted average formula)
- Filters applied (95% pct_visitors_matched threshold)
- Limitations (selection into who visits, geography confounding)
- Link to academic paper (when available)

### 7. Downloads (Coming Soon)

**Description**: Placeholder page for future data downloads.

**Content**:
- "Dataset downloads coming soon"
- Email signup for notification
- Preview of what will be available

---

## Technical Architecture

### Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | Next.js 14 (App Router) | SSR, React Server Components, same as reference sites |
| Hosting | Vercel | Free tier, automatic deploys, edge functions |
| Styling | Tailwind CSS | Rapid prototyping, responsive design |
| Maps | Mapbox GL JS or Deck.gl | WebGL-accelerated, handles millions of points |
| Charts | Recharts or D3.js | Time series, histograms, bar charts |
| Data | Static JSON + API routes | Pre-aggregated data files, on-demand filtering |
| Search | Fuse.js (client-side) | Fuzzy search for brand names |

### Data Strategy

**Challenge**: 120M POI-month rows is too large for client-side.

**Solution**: Multi-tier data architecture

1. **Static JSON (build-time)**:
   - Brand metadata (3,500 brands, ~500KB)
   - Brand monthly time series (273K rows, ~5MB)
   - MSA summaries (366 MSAs × 79 months, ~2MB)
   - Category summaries (~100 categories, ~100KB)

2. **Vercel Edge Functions (on-demand)**:
   - POI data for specific brand + MSA combinations
   - Paginated results, max 10K POIs per request

3. **External Data Store (if needed)**:
   - Vercel KV or Upstash Redis for caching
   - Or: Pre-computed tiles for map (like vector tiles)

### Map Data Strategy

**Option A: Dynamic Loading**
- User selects brand + MSA → API returns POIs → render on map
- Pros: Always fresh, flexible filtering
- Cons: Latency, API limits

**Option B: Pre-computed Vector Tiles**
- Generate Mapbox vector tiles at build time
- Pros: Fast, smooth panning/zooming
- Cons: Build complexity, storage costs, less flexible filtering

**Recommendation**: Start with Option A for MVP, migrate to Option B if performance is an issue.

---

## Page Structure

```
/                           # Landing page with key stats, featured brands
/search                     # Brand search with autocomplete
/brand/[slug]               # Brand profile page
/map                        # Interactive POI map
/map?brand=starbucks        # Map filtered to brand
/map?msa=san-francisco      # Map filtered to MSA
/map?brand=starbucks&msa=sf # Combined filter
/msa                        # MSA explorer (choropleth)
/msa/[slug]                 # Individual MSA profile
/categories                 # Category browser
/categories/[naics]         # Category detail
/rankings                   # Top Republican/Democratic brands
/methodology                # Documentation
/downloads                  # Coming soon page
```

---

## Data Preparation Tasks

Before website development, need to prepare data exports:

### Task A: Brand Summary JSON
- Source: `brand_month_partisan_lean.parquet`
- Output: `brands.json` with metadata + overall lean for each brand
- Size: ~500KB

### Task B: Brand Time Series JSON
- Source: `brand_month_partisan_lean.parquet`
- Output: `brand_timeseries/[brand_slug].json` for each brand
- Size: ~5MB total (or single file with all brands)

### Task C: MSA Summary JSON
- Source: Aggregate brand_month by MSA
- Output: `msa_summaries.json`
- Size: ~2MB

### Task D: POI Lookup Tables
- Source: POI-level data filtered to national brands
- Output: Partitioned by MSA or by brand for API access
- Storage: Vercel Blob or external (too large for git)

### Task E: Category Summaries
- Source: Aggregate brand data by NAICS/top_category
- Output: `categories.json`
- Size: ~100KB

---

## Development Phases

### Phase 1: Foundation (MVP)
1. Set up Next.js project with Tailwind
2. Create landing page with key statistics
3. Implement brand search with autocomplete
4. Build brand profile page (metadata + time series chart)
5. Add methodology page
6. Deploy to Vercel

**Deliverable**: Working site where users can search brands and see lean over time.

### Phase 2: Interactive Map
1. Integrate Mapbox GL JS
2. Build POI API endpoint (brand + MSA filter)
3. Implement map with POI markers
4. Add filter controls (brand dropdown, MSA dropdown)
5. Implement marker clustering for zoom levels
6. Add POI click popups

**Deliverable**: Interactive map showing store locations colored by partisan lean.

### Phase 3: Geographic Analysis
1. Build MSA choropleth map
2. Create MSA profile pages
3. Implement MSA comparison feature
4. Add drill-down from MSA to brands

**Deliverable**: MSA-level exploration with drill-down.

### Phase 4: Polish & Additional Features
1. Category explorer with hierarchical navigation
2. Rankings/leaderboards page
3. Dark mode support
4. Mobile responsive refinements
5. Performance optimization (lazy loading, caching)
6. Downloads page (coming soon placeholder)

**Deliverable**: Feature-complete explorer matching reference sites.

---

## Open Questions

1. **Domain name**: What URL for the site? (e.g., brandpolitics.org, consumerlean.org)
2. **Branding**: Logo, color scheme, site name?
3. **Access control**: Public or password-protected during development?
4. **POI data size**: Need to determine exact size of national brand POIs to plan storage
5. **Map provider**: Mapbox (paid after threshold) vs open-source alternatives?

---

## Effort Estimate

| Phase | Components | Notes |
|-------|------------|-------|
| Phase 1 | Foundation/MVP | Next.js setup, search, brand profiles, methodology |
| Phase 2 | Interactive Map | Mapbox integration, API endpoints, filtering |
| Phase 3 | Geographic | MSA choropleth, profiles, comparisons |
| Phase 4 | Polish | Categories, rankings, dark mode, mobile |

---

## Repository Structure

```
brand-explorer/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Landing page
│   ├── search/page.tsx    # Search page
│   ├── brand/[slug]/      # Brand profile
│   ├── map/page.tsx       # Interactive map
│   ├── msa/               # MSA pages
│   ├── categories/        # Category browser
│   ├── rankings/page.tsx  # Leaderboards
│   ├── methodology/       # Documentation
│   └── downloads/         # Coming soon
├── components/            # Reusable React components
│   ├── BrandSearch.tsx
│   ├── TimeSeriesChart.tsx
│   ├── POIMap.tsx
│   ├── MSAChoropleth.tsx
│   └── ...
├── lib/                   # Utilities, data loading
├── data/                  # Static JSON files (small)
├── public/                # Static assets
└── api/                   # API routes for dynamic data
```

---

## Dependencies on Research Pipeline

| Website Feature | Depends On |
|-----------------|------------|
| Brand search & profiles | Task 1.5a (brand_month_partisan_lean.parquet) ✅ |
| POI map | POI-level data with lat/long (need to extract) |
| MSA analysis | Task 1.6 (POI → MSA mapping) ✅ |
| Category explorer | NAICS codes in brand data ✅ |

**Blocking issue**: Need to extract lat/long for branded POIs. Current data has CBG but not exact coordinates. May need to join back to raw Advan POI data.

---

*See also: RESEARCH_PLAN.md Epic 3*
