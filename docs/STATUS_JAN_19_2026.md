# Status Update - January 19, 2026

## Overnight Jobs Status

Three SLURM jobs extracting `NORMALIZED_VISITS_BY_STATE_SCALING` from raw Advan CSVs:

| Job ID | Array | Files | Status |
|--------|-------|-------|--------|
| 31626513 | 1-1000 | 1-1000 | Running |
| 31627037 | 1-1000 (offset +1000) | 1001-2000 | Running |
| 31627039 | 1-96 (offset +2000) | 2001-2096 | Running |

**Check status:**
```bash
squeue -u maxkagan
ls /global/scratch/users/maxkagan/measuring_stakeholder_ideology/intermediate/normalized_visits_by_file/*.parquet | wc -l
```

**When all 2,096 files complete, run:**
```bash
cd /global/home/users/maxkagan/measuring_stakeholder_ideology
python3 scripts/join_normalized_visits.py
```

This adds `normalized_visits_by_state_scaling` to existing partisan lean data for proper visitor-weighted brand aggregation.

---

## What's Complete

| Component | Status | Details |
|-----------|--------|---------|
| **Partisan Lean Data** | ✅ COMPLETE | 79 files, 29GB, ~596M rows, 2019-01 to 2025-07 |
| **Entity Resolution (Brands)** | ✅ COMPLETE | 3,872 validated brand-company matches, 1.48M POIs |
| **SafeGraph Spend** | ✅ DOWNLOADED | 83 months (2019-01 to 2025-11), ~85GB |
| **Schoenmueller Brand Scores** | ✅ HAVE | 1,289 brands from social-listening.org |
| **CBG Census Data** | ✅ COMPLETE | 242,335 CBGs, 329.8M pop |

---

## Today's Priorities (After Jobs Complete)

### 1. Run Join Script
Join normalized visits to partisan lean data. Output:
`/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national_with_normalized/`

### 2. Schoenmueller Validation (Quick Win)
Compare our brand partisan lean to Schoenmueller Twitter-based scores:
- Data: `/global/home/users/maxkagan/measuring_stakeholder_ideology/reference/other_measures/schoenmueller_et_al/social-listening_PoliticalAffiliation_2022_Dec.csv`
- Use `normalized_visits_by_state_scaling` as weights for brand aggregation
- Expected output: correlation analysis, scatterplot

### 3. SafeGraph Spend Exploration
Location: `/global/scratch/users/maxkagan/01_foot_traffic_location/safegraph/poi_data_dewey_2026-01-17/spend/`
- Explore structure, coverage, quality
- Plan store performance analysis

### 4. Descriptive Analysis (Option A)
- Brand distributions by partisan lean
- Kernel density plots
- Maps
- Variance decomposition (brand vs. location)

---

## Key Data Locations

**Outputs:**
- Partisan Lean: `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/national/partisan_lean_*.parquet`
- Entity Resolution: `/global/scratch/users/maxkagan/project_oakland/outputs/entity_resolution/brand_matches_validated.parquet`

**Inputs:**
- Advan Raw: `/global/scratch/users/maxkagan/01_foot_traffic_location/advan/foot_traffic_monthly_complete_2026-01-12/`
- SafeGraph Spend: `/global/scratch/users/maxkagan/01_foot_traffic_location/safegraph/poi_data_dewey_2026-01-17/spend/`

---

## Deprioritized for Now

- **Option G (Temporal)**: Limited by data starting in 2019
- **Option L (Review Sentiment)**: Lower priority
- **Singleton POI matching**: After branded analysis complete

---

## Scripts

- Extraction: `scripts/extract_normalized_visits.py`
- Join: `scripts/join_normalized_visits.py`
- SLURM: `scripts/slurm/extract_normalized_visits*.slurm`

---

*Generated 2026-01-18 ~21:20 PST*
