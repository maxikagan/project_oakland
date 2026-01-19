# Research Plan

**Goal**: Job market paper on stakeholder ideology (Fall 2026)

---

## Current Priorities

### Immediate (After overnight jobs complete)
1. **Schoenmueller validation** - Compare our brand partisan lean to Twitter-based scores (1,289 brands)
2. **SafeGraph Spend exploration** - Assess data for store performance analysis
3. **Descriptive analysis** - Brand distributions, kernel density plots, variance decomposition

### Next Phase
4. **Excess partisan lean** - Gravity model controlling for geography
5. **Entity resolution for singletons** - Match unbranded POIs to PAW

---

## Research Options (Prioritized)

| Priority | Option | Description | Data Ready? |
|----------|--------|-------------|-------------|
| ⭐ HIGH | A | Descriptive employee-consumer alignment | ✅ Yes |
| ⭐ HIGH | B | Schoenmueller validation | ✅ Yes |
| ⭐ HIGH | D | Site-level spending (SafeGraph) | ✅ Yes |
| HIGH | H | Worker mobility toward aligned firms | Needs PAW linkage |
| HIGH | I | Competitive dynamics / market share | Needs market definition |
| HIGH | K | Geographic expansion sequencing | Needs OPENED_ON analysis |
| MEDIUM | C | Mismatch → outcomes | Needs DV collection |
| LOW | G | Temporal dynamics | Limited (data starts 2019) |
| LOW | L | Review sentiment | Lower priority |

---

## Data Status

| Component | Status | Location |
|-----------|--------|----------|
| Partisan Lean | ✅ 79 months | `outputs/national/partisan_lean_*.parquet` |
| Entity Resolution | ✅ 3,872 brands | `project_oakland/outputs/entity_resolution/brand_matches_validated.parquet` |
| SafeGraph Spend | ✅ 83 months | `01_foot_traffic_location/safegraph/.../spend/` |
| Schoenmueller | ✅ 1,289 brands | `reference/other_measures/schoenmueller_et_al/` |
| Normalized Visits | 🔄 Extracting | `intermediate/normalized_visits_by_file/` |

---

## Key Methodology

### Brand Aggregation
Use `normalized_visits_by_state_scaling` as weights to avoid sampling bias:
```
brand_lean = Σ(rep_lean_i × normalized_visits_i) / Σ(normalized_visits_i)
```

### Excess Partisan Lean
Gravity model with NAICS 4-digit categories:
```
excess_lean = actual_lean - expected_lean_from_gravity
```

### Validation Approach
Compare to Schoenmueller Twitter-based brand ideology scores (correlation, scatterplot)

---

## Output Schema

Key columns in partisan lean files:
- `placekey` - POI identifier
- `date_range_start` - Month
- `brand`, `naics_code`, `top_category` - Classification
- `rep_lean_2020`, `rep_lean_2016` - Partisan lean
- `raw_visitor_counts` - Visitor count
- `normalized_visits_by_state_scaling` - Weight for aggregation (after join)

---

## Deprioritized

- **Option G (Temporal)**: Data starts 2019, misses 2016 polarization surge
- **Option L (Reviews)**: Lower priority, high effort
- **Singleton matching**: After branded analysis complete

---

*See `reference/FULL_RESEARCH_AGENDA.md` for complete details*
