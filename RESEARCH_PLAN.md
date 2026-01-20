# Research Plan

**Goal**: Job market paper on stakeholder ideology (Fall 2026)

---

## Repository Structure

```
scripts/
├── 01_data_prep/           # Election data, CBG lookup, schema
├── 02_partisan_lean/       # Core computation pipeline
├── 03_entity_resolution/   # Brand/company matching
├── 04_validation/          # Schoenmueller comparison
├── 05_descriptive/         # Brand distributions, R reports
├── 06_performance/         # SafeGraph Spend, POI lifecycle
├── 07_causal/              # Gravity model, DiD, etc.
└── archive/                # Old/superseded scripts
```

---

## Epics & Tasks

### Epic 1: Data Pipeline 🔄 IN PROGRESS
Core data infrastructure for partisan lean measurement.
**Scripts**: `scripts/01_data_prep/`, `scripts/02_partisan_lean/`, `scripts/03_entity_resolution/`
**Detailed plan**: `docs/plans/data_pipeline_plan.md`

#### Phase 1: POI-Level Partisan Lean (COMPLETE)
| Task | Status | Notes |
|------|--------|-------|
| 1.1 Partisan lean computation | ✅ Done | 79 months, 596M POI-month rows. Weighted avg of CBG election results by visitor origin. |
| 1.2 Extract normalized visits | ✅ Done | 2,096 raw Advan files → extracted `normalized_visits_by_state_scaling` column |
| 1.3 Join normalized visits | ✅ Done | Merged normalized visits into partisan lean data (79 monthly parquet files) |

#### Phase 2: National Brands (COMPLETE)
| Task | Status | Notes |
|------|--------|-------|
| 1.4 Entity resolution (national brands) | ✅ Done | Matched 3,872 Advan brands → companies (gvkey, ticker, rcid). 1.48M POIs covered. |
| 1.5a Aggregate to brand × month | ✅ Done | 273K brand-months, 3,543 brands. Weighted avg using normalized_visits. Output: `brand_month_partisan_lean.parquet` |

#### Phase 3: Singletons / Unbranded POIs (IN PROGRESS)
| Task | Status | Notes |
|------|--------|-------|
| 1.6 POI → MSA mapping | ✅ Done | 6.31M POIs mapped to 366 MSAs via CBG crosswalk |
| 1.7 Aggregate to name × MSA × month | ⬚ Pending | Group unbranded POIs by (poi_name, msa, year_month). Preserves `total_normalized_visits` for later rollup. |
| 1.8 (Optional) Link to PAW for cross-MSA rollup | ⬚ Pending | If PAW identifies same company across MSAs, can re-aggregate using preserved weights. See Epic 6. |

#### Phase 4: Documentation
| Task | Status | Notes |
|------|--------|-------|
| 1.9 Document aggregation methodology | ⬚ Pending | LaTeX appendix: data sources, filters (95% pct_visitors_matched), weighted avg formula, singleton approach |

**Singleton aggregation approach**: We aggregate unbranded POIs by `name + MSA` (not requiring PAW). This avoids systematic exclusion of businesses not in PAW (small businesses, sole proprietors). We preserve `total_normalized_visits` at each level so that if PAW later identifies the same company across multiple MSAs, we can correctly re-aggregate. See `docs/plans/singleton_aggregation_plan.md` for details.

### Epic 2: Validation (Schoenmueller Comparison) ✅ COMPLETE
Validate our measure against external benchmarks.
**Scripts**: `scripts/04_validation/`

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Load Schoenmueller data | ✅ Done | 1,289 brands, Rep 0.04-0.98 |
| 2.2 Match brands to Schoenmueller | ✅ Done | Semantic embeddings (text-embedding-3-large) + Jaro-Winkler + manual verification. 1,036 candidate pairs → 662 TRUE matches, 374 FALSE. Final sample: 283 brands with foot traffic data. |
| 2.3 Correlation analysis | ✅ Done | **r=0.27, p<0.001, ρ=0.40**. National brands (31+ states): r=0.32. Regional: r=0.21. Local: r=0.18 (n.s.). |
| 2.4 Divergence analysis | ✅ Done | Twitter extremity explains divergence (r=0.72). Trump properties most divergent (92% R Twitter vs 36% R foot traffic). High-traffic brands align well. |
| 2.5 Generate validation outputs | ✅ Done | Scatter plot PNG/PDF in `outputs/validation/` and `paper/figures/` |
| 2.6 Generate LaTeX table rows | ✅ Done | Full 283-brand comparison table for appendix |
| 2.7 Document matching methodology | ✅ Done | LaTeX appendix updated with methodology, stats, conclusion |

**Key finding**: Moderate convergent validity. Twitter captures performative political consumption (self-selection); foot traffic captures routine commercial behavior. Measures correlate positively but are not interchangeable.

### Epic 3: Descriptive Analysis 🟡 PARTIALLY READY
Document patterns in consumer partisan lean.
**Scripts**: `scripts/05_descriptive/`
**Website plan**: `docs/plans/brand_explorer_website_plan.md`

#### Phase 1: Static Analysis
| Task | Status | Notes |
|------|--------|-------|
| 3.1 Brand distributions | ⬚ Pending | Histogram, KDE plots |
| 3.2 Variance decomposition | ⬚ Pending | Brand vs. location effects |
| 3.3 Geographic patterns | ⬚ Pending | Maps by state/MSA |
| 3.4 Category comparisons | ⬚ Pending | By NAICS, top_category |
| 3.5 Top/bottom brand rankings | ⬚ Pending | Most R vs. most D brands |
| 3.6 Document descriptive methods | ⬚ Pending | LaTeX appendix: summary stats, decomposition approach |

*Can start with national brands (3,543). Full analysis needs singletons (Task 1.7).*

#### Phase 2: Interactive Website (Brand Partisan Lean Explorer)
Public Vercel website for data exploration. Pattern: politicsatwork.org / whatisstrategy.org
**Repo**: Separate repo (to be created)
**Replaces**: `dashboard/` (Streamlit prototype requiring SSH tunnel)

| Task | Status | Notes |
|------|--------|-------|
| 3.7 Data export for website | ⬚ Pending | JSON exports: brand summaries, time series, MSA summaries, POI data (partitioned) |
| 3.8 Website Phase 1 (MVP) | ⬚ Pending | Next.js setup, brand search, brand profiles with time series, methodology page |
| 3.9 Website Phase 2 (Map) | ⬚ Pending | Interactive POI map with Mapbox. Filter by brand, MSA, or both. Color by partisan lean. |
| 3.10 Website Phase 3 (Geographic) | ⬚ Pending | MSA choropleth, MSA profiles, drill-down from MSA to brands |
| 3.11 Website Phase 4 (Polish) | ⬚ Pending | Category explorer, rankings, dark mode, downloads (coming soon) |

**Key features**:
- **Brand search & profiles**: Search ~3,500 brands, view partisan lean over 79 months vs category benchmarks
- **Interactive POI map**: Store locations colored by lean, filter by brand + MSA, see within-MSA variation
- **MSA analysis**: Choropleth map, compare brands within same MSA
- **Rankings**: Most Republican / Democratic brands

*Depends on: Task 1.5a (brand-month data) ✅, POI coordinates (need to extract)*

### Epic 4: Store Performance (SafeGraph Spend) 🟡 PARTIALLY READY
Link partisan lean to business outcomes using SafeGraph Spend.
**Scripts**: `scripts/06_performance/`

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Explore SafeGraph Spend | ✅ Done | 83 months, 93% POI overlap |
| 4.2 Match to partisan lean | ⬚ Pending | Join on PLACEKEY |
| 4.3 Within-store TWFE | ⬚ Pending | Spending ~ lean × salience |
| 4.4 Event studies | ⬚ Pending | Elections, Dobbs, etc. |
| 4.5 Document performance methods | ⬚ Pending | LaTeX appendix: SafeGraph Spend join, TWFE spec |

*Can start with national brands. Full coverage needs singletons (Task 1.7).*

### Epic 5: Excess Partisan Lean (Gravity Model) 🟡 PARTIALLY READY
Control for geography using gravity model.
**Scripts**: `scripts/07_causal/` (gravity model)

| Task | Status | Notes |
|------|--------|-------|
| 5.1 Build gravity model | ⬚ Pending | Distance decay, population |
| 5.2 Category-specific parameters | ⬚ Pending | NAICS 4-digit |
| 5.3 Compute expected lean | ⬚ Pending | From gravity predictions |
| 5.4 Calculate excess lean | ⬚ Pending | Actual - expected |
| 5.5 Document gravity model | ⬚ Pending | LaTeX appendix: model spec, distance decay, category params |

*Can prototype with national brands. Full geographic coverage needs singletons (Task 1.7).*

### Epic 6: Employee-Consumer Alignment ⬚ BLOCKED
Link consumer partisan lean to Politics at Work employee ideology data.
**Scripts**: `scripts/07_causal/`
**Detailed plan**: `docs/plans/entity_resolution_paw_linkage.md`

| Task | Status | Notes |
|------|--------|-------|
| 6.1 PAW Company × MSA table | ✅ Done | 4.1M companies, 366 MSAs. Source: Politics at Work voter registration + employment records. |
| 6.2 Link national brands to PAW | ✅ Done | Via brand entity resolution (Task 1.4). 3,872 brands matched to rcid. |
| 6.3 Link singletons to PAW | ⬚ Pending | Match name×MSA entities (from Task 1.7) to PAW companies. Enables cross-MSA rollup for regional chains. |
| 6.4 Compute employee partisanship | ⬚ Pending | Aggregate PAW VR scores (voter registration) by company. |
| 6.5 Employee-consumer alignment analysis | ⬚ Pending | Correlate employee partisan lean with consumer partisan lean at company level. |
| 6.6 Document PAW linkage | ⬚ Pending | LaTeX appendix: PAW data description, VR score methodology, MSA matching, coverage limitations. |

*Depends on: Epic 1 completion (especially Task 1.7 for singletons)*

**PAW coverage limitation**: PAW only includes companies with employees who have voter registration records. This systematically excludes sole proprietors, very small businesses, and businesses with unregistered employees. We document this as a limitation and note that the name×MSA aggregation in Epic 1 provides broader coverage for consumer-side analysis.

### Epic 7: Causal Identification (Later Phase) ⬚ NOT STARTED
Establish causal relationships.
**Scripts**: `scripts/07_causal/`

| Task | Status | Notes |
|------|--------|-------|
| 7.1 Political salience shocks | ⬚ Pending | DiD around elections |
| 7.2 PCI interaction effects | ⬚ Pending | Partisan Conflict Index |
| 7.3 Geographic expansion | ⬚ Pending | Entry patterns |
| 7.4 Worker mobility | ⬚ Pending | Job transitions |
| 7.5 Document causal methods | ⬚ Pending | LaTeX appendix: DiD design, PCI interaction, identification |

---

## Current Sprint

**Focus**: Epic 3 (descriptive analysis) + Epic 1 Phase 3 (singletons) in parallel

**Completed recently**:
- ✅ Epic 2 COMPLETE: Schoenmueller validation (r=0.27, p<0.001)
  - Brand matching: semantic embeddings + Jaro-Winkler + manual verification
  - 283 brands matched with foot traffic data
  - Scatter plot, correlation stats, divergence analysis all complete
  - LaTeX appendix fully updated with methodology and results
- ✅ Task 1.5a: Brand-month aggregation (273K rows, 3,543 brands)

**In progress**:
- 🔄 Task 1.7: Singleton entity resolution (pilot job for Columbus OH)

**Next up**:
1. Epic 3 Phase 2: Interactive website (Brand Partisan Lean Explorer)
   - Task 3.7: Data export for website (JSON files)
   - Task 3.8: Website MVP (Next.js, brand search, profiles)
   - Task 3.9: Interactive POI map
2. Epic 3 Phase 1: Static descriptive analysis
   - Task 3.1: Brand distributions (histogram, KDE)
   - Task 3.5: Top/bottom brand rankings
3. Task 1.9: Document aggregation methodology in appendix
4. Epic 4: Store performance (SafeGraph Spend linkage)

---

## Data Status

| Component | Status | Location |
|-----------|--------|----------|
| **POI-Level Data** | | |
| Partisan Lean + Normalized | ✅ 79 months, 596M rows | `outputs/national_with_normalized/` |
| POI → MSA Mapping | ✅ 6.31M POIs | `outputs/entity_resolution/unbranded_pois_by_msa/` |
| **National Brands** | | |
| Entity Resolution | ✅ 3,872 brands → companies | `outputs/entity_resolution/brand_matches_validated.parquet` |
| Brand × Month Aggregated | ✅ 273K rows, 3,543 brands | `outputs/brand_month_aggregated/brand_month_partisan_lean.parquet` |
| **Singletons** | | |
| Name × MSA × Month Aggregated | ⬚ Pending | `outputs/singleton_name_msa_aggregated/` (planned) |
| **External Data** | | |
| SafeGraph Spend | ✅ 83 months | `01_foot_traffic_location/safegraph/.../spend/` |
| Schoenmueller Twitter Scores | ✅ 1,289 brands | `reference/other_measures/schoenmueller_et_al/` |
| PCI Time Series | ✅ 1981-2025 | `reference/partisan_conflict_index.csv` |
| PAW Company × MSA | ✅ 4.1M companies | `project_oakland/outputs/paw_company_msa.parquet` |
| **Validation Outputs** | | |
| Validation Comparison | ✅ 283 brands | `outputs/validation/validation_comparison.csv` |
| Labeled Matches | ✅ 1,036 pairs | `outputs/validation/labeled_matches.csv` |
| Scatter Plot | ✅ PNG/PDF | `outputs/validation/validation_scatter.pdf`, `paper/figures/` |
| Divergent Brands | ✅ Top 20 | `outputs/validation/divergent_brands.csv` |

---

## Key Methodology

### Brand Aggregation
Use `normalized_visits_by_state_scaling` as weights:
```
brand_lean = Σ(rep_lean_i × normalized_visits_i) / Σ(normalized_visits_i)
```

### Excess Partisan Lean
Gravity model with NAICS 4-digit categories:
```
excess_lean = actual_lean - expected_lean_from_gravity
```

---

## Deprioritized

- **Option G (Temporal)**: Data starts 2019, misses 2016 polarization
- **Option L (Reviews)**: Lower priority, high effort

---

*Last updated: 2026-01-20*
*See `reference/FULL_RESEARCH_AGENDA.md` for complete research option details*
