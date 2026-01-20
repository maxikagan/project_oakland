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

### Epic 1: Data Pipeline ✅ NEARLY COMPLETE
Core data infrastructure for partisan lean measurement.
**Scripts**: `scripts/01_data_prep/`, `scripts/02_partisan_lean/`, `scripts/03_entity_resolution/`

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Partisan lean computation | ✅ Done | 79 months, 596M rows |
| 1.2 Entity resolution (brands) | ✅ Done | 3,872 brands, 1.48M POIs |
| 1.3 Extract normalized visits | ✅ Done | 2,096 files extracted |
| 1.4 Join normalized visits | ✅ Done | 79 files completed |
| 1.5 Aggregate brand-level lean | 🔄 In Progress | Job 31705749 running |

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

*Blocked by: Epic 2 validation*

### Epic 6: Employee-Consumer Alignment (Singleton Matching) 🔄 PREREQUISITES DONE
Link to Politics at Work employee data.
**Scripts**: `scripts/03_entity_resolution/` (singletons), `scripts/07_causal/`

| Task | Status | Notes |
|------|--------|-------|
| 6.0a PAW Company × MSA table | ✅ Done | 4.1M companies, 366 MSAs |
| 6.0b POI → MSA mapping | ✅ Done | 6.31M POIs with crosswalk |
| 6.1 Singleton embedding script | 🔄 In Progress | Pilot job 31705616 (Columbus OH) |
| 6.2 Link brands to PAW employers | ✅ Done | Via brand entity resolution |
| 6.3 Compute employee partisanship | ⬚ Pending | From PAW VR scores |
| 6.4 Alignment correlation | ⬚ Pending | Employee vs. consumer |

### Epic 7: Causal Identification (Later Phase) ⬚ NOT STARTED
Establish causal relationships.
**Scripts**: `scripts/07_causal/`

| Task | Status | Notes |
|------|--------|-------|
| 7.1 Political salience shocks | ⬚ Pending | DiD around elections |
| 7.2 PCI interaction effects | ⬚ Pending | Partisan Conflict Index |
| 7.3 Geographic expansion | ⬚ Pending | Entry patterns |
| 7.4 Worker mobility | ⬚ Pending | Job transitions |

---

## Current Sprint

**Focus**: Epic 1.5 (critical blocker) → Epics 2, 3, 4

**Immediate next steps**:
1. **Task 1.5: Aggregate brand-level lean** (unblocks Epics 2, 3, 4)
2. Task 2.2: Complete brand matching (semantic similarity - in progress)
3. Task 2.3-2.5: Correlation analysis, divergence, LaTeX appendix
4. Tasks 3.1-3.2: Brand distributions and variance decomposition

---

## Data Status

| Component | Status | Location |
|-----------|--------|----------|
| Partisan Lean | ✅ 79 months | `outputs/national/partisan_lean_*.parquet` |
| Partisan Lean + Normalized | ✅ 79 months | `outputs/national_with_normalized/` |
| Entity Resolution | ✅ 3,872 brands | `outputs/entity_resolution/brand_matches_validated.parquet` |
| POI → MSA Mapping | ✅ 6.31M POIs | `outputs/entity_resolution/unbranded_pois_by_msa/` |
| SafeGraph Spend | ✅ 83 months | `01_foot_traffic_location/safegraph/.../spend/` |
| Schoenmueller | ✅ 1,289 brands | `reference/other_measures/schoenmueller_et_al/` |
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
