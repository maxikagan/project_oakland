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

### Epic 2: Validation (Schoenmueller Comparison) 🔄 IN PROGRESS
Validate our measure against external benchmarks.
**Scripts**: `scripts/04_validation/`

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Load Schoenmueller data | ✅ Done | 1,289 brands, Rep 0.04-0.98 |
| 2.2 Match brands to Schoenmueller | 🔄 In Progress | Semantic similarity approach |
| 2.3 Correlation analysis | ⬚ Pending | Scatter plot, R² |
| 2.4 Divergence analysis | ⬚ Pending | Where/why do measures differ? |
| 2.5 Generate validation outputs | ⬚ Pending | Scatter plot PNG/PDF, correlation stats |
| 2.6 Generate LaTeX table rows | ⬚ Pending | Full brand comparison table for appendix |
| 2.7 Document matching methodology | ⬚ Pending | LaTeX appendix: semantic similarity + Claude review |

*Blocked by: 1.5 (brand-level aggregation)*

### Epic 3: Descriptive Analysis ⬚ BLOCKED
Document patterns in consumer partisan lean.
**Scripts**: `scripts/05_descriptive/`

| Task | Status | Notes |
|------|--------|-------|
| 3.1 Brand distributions | ⬚ Pending | Histogram, KDE plots |
| 3.2 Variance decomposition | ⬚ Pending | Brand vs. location effects |
| 3.3 Geographic patterns | ⬚ Pending | Maps by state/MSA |
| 3.4 Category comparisons | ⬚ Pending | By NAICS, top_category |
| 3.5 Top/bottom brand rankings | ⬚ Pending | Most R vs. most D brands |
| 3.6 Document descriptive methods | ⬚ Pending | LaTeX appendix: summary stats, decomposition approach |

*Blocked by: 1.5 (brand-level aggregation)*

### Epic 4: Store Performance (SafeGraph Spend) ⬚ BLOCKED
Link partisan lean to business outcomes using SafeGraph Spend.
**Scripts**: `scripts/06_performance/`

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Explore SafeGraph Spend | ✅ Done | 83 months, 93% POI overlap |
| 4.2 Match to partisan lean | ⬚ Pending | Join on PLACEKEY |
| 4.3 Within-store TWFE | ⬚ Pending | Spending ~ lean × salience |
| 4.4 Event studies | ⬚ Pending | Elections, Dobbs, etc. |
| 4.5 Document performance methods | ⬚ Pending | LaTeX appendix: SafeGraph Spend join, TWFE spec |

*Blocked by: 1.5 (brand-level aggregation)*

### Epic 5: Excess Partisan Lean (Gravity Model) ⬚ BLOCKED
Control for geography using gravity model.
**Scripts**: `scripts/07_causal/` (gravity model)

| Task | Status | Notes |
|------|--------|-------|
| 5.1 Build gravity model | ⬚ Pending | Distance decay, population |
| 5.2 Category-specific parameters | ⬚ Pending | NAICS 4-digit |
| 5.3 Compute expected lean | ⬚ Pending | From gravity predictions |
| 5.4 Calculate excess lean | ⬚ Pending | Actual - expected |
| 5.5 Document gravity model | ⬚ Pending | LaTeX appendix: model spec, distance decay, category params |

*Blocked by: Epic 2 validation*

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

**Focus**: Epic 2 (validation) + Epic 1 Phase 3 (singletons) in parallel

**Completed this session**:
- ✅ Task 1.5a: Brand-month aggregation (273K rows, 3,543 brands)
- ✅ Task 2.1: Load Schoenmueller data (1,289 brands)

**In progress**:
- 🔄 Task 2.2: Schoenmueller brand matching (semantic similarity + manual Claude review)
  - 257 exact matches, 411 contains matches, 368 under manual review
- 🔄 Task 1.7: Singleton entity resolution (pilot job submitted for Columbus OH)

**Next up**:
1. Task 2.3-2.6: Correlation analysis, divergence, validation outputs, LaTeX tables
2. Task 2.7: Document matching methodology in appendix
3. Task 3.1-3.2: Descriptive analysis (now unblocked)
4. Task 1.8: Document aggregation methodology in appendix

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
