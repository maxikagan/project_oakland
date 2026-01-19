# Claude Code Instructions

## Rules
- **No compute on login node** - Always use SLURM batch jobs
- **Code review before running** - Use Code Reviewer agent (see AGENTS.md)
- **Log to SESSION_LOG.md** - Before/after jobs, include job IDs
- Data fidelity paramount - document all steps clearly

## Savio HPC
- **Account**: fc_basicperms
- **Partitions**: savio2 (64GB), savio3 (95GB), savio3_bigmem (386GB)
- **Array max**: 1001 tasks (split larger jobs)

## Project Goal
Partisan lean of business visitors → job market paper (Fall 2026)

## Current Priorities
1. Schoenmueller validation (compare to Twitter-based brand scores)
2. SafeGraph Spend exploration (store performance)
3. Descriptive analysis (brand distributions)

See `RESEARCH_PLAN.md` for details, `reference/FULL_RESEARCH_AGENDA.md` for complete context.

## Key Data Paths

**Outputs** (scratch):
- Partisan lean: `measuring_stakeholder_ideology/outputs/national/partisan_lean_*.parquet`
- Entity resolution: `project_oakland/outputs/entity_resolution/brand_matches_validated.parquet`

**Inputs** (scratch):
- Advan raw: `01_foot_traffic_location/advan/foot_traffic_monthly_complete_2026-01-12/`
- SafeGraph Spend: `01_foot_traffic_location/safegraph/poi_data_dewey_2026-01-17/spend/`
- Schoenmueller: `measuring_stakeholder_ideology/reference/other_measures/schoenmueller_et_al/`

**All scratch paths**: `/global/scratch/users/maxkagan/`
**All home paths**: `/global/home/users/maxkagan/`

## Key Decisions
- Brand aggregation weight: `normalized_visits_by_state_scaling`
- Category grouping: NAICS 4-digit
- Election data: Both 2016 and 2020
