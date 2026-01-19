# Research Plan

**Goal**: Job market paper on stakeholder ideology (Fall 2026)

---

## Epics & Tasks

### Epic 1: Data Pipeline ✅ COMPLETE
Core data infrastructure for partisan lean measurement.

| Task | Status | Notes |
|------|--------|-------|
| 1.1 Partisan lean computation | ✅ Done | 79 months, 596M rows |
| 1.2 Entity resolution (brands) | ✅ Done | 3,872 brands, 1.48M POIs |
| 1.3 Extract normalized visits | ✅ Done | 2,096 files extracted |
| 1.4 Join normalized visits | 🔄 Running | Job 31677682 |

### Epic 2: Validation (Option B)
Validate our measure against external benchmarks.

| Task | Status | Notes |
|------|--------|-------|
| 2.1 Load Schoenmueller data | ⬚ Pending | 1,289 brands available |
| 2.2 Aggregate brand-level lean | ⬚ Pending | Use normalized_visits weights |
| 2.3 Match brands to Schoenmueller | ⬚ Pending | Fuzzy match brand names |
| 2.4 Correlation analysis | ⬚ Pending | Scatter plot, R² |
| 2.5 Divergence analysis | ⬚ Pending | Where/why do measures differ? |

### Epic 3: Descriptive Analysis (Option A)
Document patterns in consumer partisan lean.

| Task | Status | Notes |
|------|--------|-------|
| 3.1 Brand distributions | ⬚ Pending | Histogram, KDE plots |
| 3.2 Variance decomposition | ⬚ Pending | Brand vs. location effects |
| 3.3 Geographic patterns | ⬚ Pending | Maps by state/MSA |
| 3.4 Category comparisons | ⬚ Pending | By NAICS, top_category |
| 3.5 Top/bottom brand rankings | ⬚ Pending | Most R vs. most D brands |

### Epic 4: Store Performance (Option D)
Link partisan lean to business outcomes using SafeGraph Spend.

| Task | Status | Notes |
|------|--------|-------|
| 4.1 Explore SafeGraph Spend | ⬚ Pending | Structure, coverage, quality |
| 4.2 Match to partisan lean | ⬚ Pending | Join on PLACEKEY |
| 4.3 Within-store TWFE | ⬚ Pending | Spending ~ lean × salience |
| 4.4 Event studies | ⬚ Pending | Elections, Dobbs, etc. |

### Epic 5: Excess Partisan Lean
Control for geography using gravity model.

| Task | Status | Notes |
|------|--------|-------|
| 5.1 Build gravity model | ⬚ Pending | Distance decay, population |
| 5.2 Category-specific parameters | ⬚ Pending | NAICS 4-digit |
| 5.3 Compute expected lean | ⬚ Pending | From gravity predictions |
| 5.4 Calculate excess lean | ⬚ Pending | Actual - expected |

### Epic 6: Employee-Consumer Alignment (Option A extended)
Link to Politics at Work employee data.

| Task | Status | Notes |
|------|--------|-------|
| 6.1 Entity resolution (singletons) | ⬚ Pending | Match unbranded POIs |
| 6.2 Link brands to PAW employers | ⬚ Pending | Via entity resolution |
| 6.3 Compute employee partisanship | ⬚ Pending | From PAW VR scores |
| 6.4 Alignment correlation | ⬚ Pending | Employee vs. consumer |

### Epic 7: Causal Identification (Later Phase)
Establish causal relationships.

| Task | Status | Notes |
|------|--------|-------|
| 7.1 Political salience shocks | ⬚ Pending | DiD around elections |
| 7.2 PCI interaction effects | ⬚ Pending | Partisan Conflict Index |
| 7.3 Geographic expansion | ⬚ Pending | Option K - entry patterns |
| 7.4 Worker mobility | ⬚ Pending | Option H - job transitions |

---

## Current Sprint

**Focus**: Epics 2-4 (Validation, Descriptive, Store Performance)

**Immediate next steps** (after join job completes):
1. Task 2.1-2.4: Schoenmueller validation
2. Task 4.1: SafeGraph Spend exploration
3. Task 3.1-3.2: Brand distributions and variance decomposition

---

## Data Status

| Component | Status | Location |
|-----------|--------|----------|
| Partisan Lean | ✅ 79 months | `outputs/national/partisan_lean_*.parquet` |
| Partisan Lean + Normalized | 🔄 Building | `outputs/national_with_normalized/` |
| Entity Resolution | ✅ 3,872 brands | `outputs/entity_resolution/brand_matches_validated.parquet` |
| SafeGraph Spend | ✅ 83 months | `01_foot_traffic_location/safegraph/.../spend/` |
| Schoenmueller | ✅ 1,289 brands | `reference/other_measures/schoenmueller_et_al/` |
| PCI Time Series | ✅ 1981-2025 | `data/partisan_conflict_index.csv` |

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
- **Singleton matching**: After branded analysis complete

---

*See `reference/FULL_RESEARCH_AGENDA.md` for complete research option details*
