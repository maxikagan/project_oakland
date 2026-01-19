# National Scale-Up: Quick Start Guide

## What Was Implemented

Complete Python/SLURM pipeline for scaling Ohio 2023 pilot analysis to all 50 US states using 2024 Advan foot traffic data.

**6 processing steps** that will generate:
- POI-level partisan lean estimates for ~15-20M observations
- 12 monthly parquet files (2024-01 through 2024-12)
- Comprehensive diagnostic reports on data quality

---

## Before You Run

### 1. Code Review (MANDATORY per CLAUDE.md)

Before submitting the pipeline, review the code with the Code Reviewer agent:

```bash
cd /global/home/users/maxkagan/project_oakland
# Review each script:
# - scripts/01_02_election_data_setup.py
# - scripts/03_filter_advan_by_state.py
# - scripts/04_compute_partisan_lean.py
# - scripts/05_combine_and_partition.py
# - scripts/06_generate_diagnostics.py
```

### 2. Check Data Files Exist

```bash
# Election data (should have 50+ state zips)
ls /global/scratch/users/maxkagan/election_results_geocoded/ | wc -l

# 2024 Advan data (should have ~440 parquet files)
ls /global/scratch/users/maxkagan/project_oakland/advan_foot_traffic_2024_2026-01-12/foot-traffic-monthly-2024/ | wc -l
```

Both should show files present. If missing, data download may still be in progress.

---

## How to Run

### Option 1: Submit Full Pipeline (Recommended)

```bash
cd /global/home/users/maxkagan/project_oakland
bash scripts/submit_national_scaleup.sh
```

This automatically:
- Creates SLURM job scripts for each step
- Sets up job dependencies (sequential execution)
- Configures array jobs for parallelization
- Logs all submissions to `logs/national_scaleup/submission.log`

### Option 2: Run Individual Steps (Manual Testing)

```bash
# Step 1-2: Unzip elections and build CBG lookup
sbatch -A fc_basicperms -p savio3 -t 02:00:00 \
  --wrap="cd /global/home/users/maxkagan/project_oakland/scripts && python3 01_02_election_data_setup.py"

# Step 3: Filter Advan data for one state (example: CA)
sbatch -A fc_basicperms -p savio3_bigmem -t 06:00:00 \
  --wrap="cd /global/home/users/maxkagan/project_oakland/scripts && python3 03_filter_advan_by_state.py CA"

# Step 4: Compute partisan lean for one state (example: CA)
sbatch -A fc_basicperms -p savio3_bigmem -t 08:00:00 \
  --wrap="cd /global/home/users/maxkagan/project_oakland/scripts && python3 04_compute_partisan_lean.py CA"
```

---

## Monitor Progress

### Check Queue Status
```bash
squeue -u maxkagan
```

### View Submission Log
```bash
tail -f /global/home/users/maxkagan/project_oakland/logs/national_scaleup/submission.log
```

### View Step Logs (after submission)
```bash
ls -lh /global/home/users/maxkagan/project_oakland/logs/national_scaleup/step*.log
tail -f /global/home/users/maxkagan/project_oakland/logs/national_scaleup/step4_compute_partisan_0.log  # View Step 4 task 1
```

### Check Intermediate Output
```bash
# After Step 1-2
ls /global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national.parquet

# After Step 3
ls /global/scratch/users/maxkagan/project_oakland/intermediate/advan_2024_filtered/*/

# After Step 4
ls /global/scratch/users/maxkagan/project_oakland/intermediate/advan_2024_partisan/

# After Step 5 (Final Output!)
ls /global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean/national_2024/

# After Step 6 (Diagnostics)
ls /global/scratch/users/maxkagan/project_Oakland/outputs/diagnostics/
```

---

## Expected Outputs

### Main Output (from Step 5)
**Location**: `/global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean/national_2024/`

**12 monthly files**:
- `2024-01.parquet` (Jan 2024)
- `2024-02.parquet` (Feb 2024)
- ...
- `2024-12.parquet` (Dec 2024)

**Each file contains**:
- `placekey`: POI identifier
- `date_range_start`: Month start date
- `brand`, `top_category`, `sub_category`, `naics_code`: Location descriptors
- `city`, `region`: Location
- `parent_placekey`, `median_dwell`: Location attributes
- `rep_lean`: Two-party Republican share (0-1) weighted by visitors
- `total_visitors`: Matched visitor count
- `unmatched_visitors`: Unmatched visitor count (diagnostic)
- `pct_visitors_matched`: % of visitors matched to CBG lookup

### Diagnostic Output (from Step 6)
**Location**: `/global/scratch/users/maxkagan/project_oakland/outputs/diagnostics/`

**CSV Reports**:
- `unmatched_cbgs_by_state.csv`: States with unmatched CBGs
- `top_unmatched_cbgs.csv`: Top 100 CBGs not in election data
- `data_quality_metrics_by_state.csv`: Coverage % and partisan lean by state
- `final_dataset_stats_by_month.csv`: Summary statistics by month

---

## Timeline & Resources

### Compute Time
| Step | Partition | Time | Notes |
|------|-----------|------|-------|
| 0-2 | savio3 | 2.25 hrs | Sequential (schema + election setup) |
| 3 | savio3_bigmem | 6 hrs | Array job (50 parallel tasks) |
| 4 | savio3_bigmem | 8 hrs | Array job (50 parallel tasks) |
| 5 | savio3_bigmem | 4 hrs | Single job (combine + partition) |
| 6 | savio3 | 2 hrs | Single job (diagnostics) |

**Total wall time**: ~25 hours (with parallelization)
**Actual job duration**: ~10-15 hours (due to array parallelization)

### Storage Requirements
- **Intermediate**: ~500 GB (can be deleted after Step 5 completes)
- **Final output**: ~30-50 GB (keep for analysis)
- **Total scratch needed**: ~600-700 GB (currently available)

---

## Troubleshooting

### Job Fails with "File not found"
1. Check previous step completed: `squeue -u maxkagan`
2. Verify output directory exists: `ls /global/scratch/users/maxkagan/project_oakland/intermediate/`
3. If missing, step may have failed silently - check logs

### Array Job Fails for Some States
1. Check which states failed: `sacct -u maxkagan`
2. Resubmit failed states individually:
   ```bash
   sbatch -A fc_basicperms -p savio3_bigmem -t 06:00:00 \
     --wrap="cd /global/home/users/maxkagan/project_oakland/scripts && python3 04_compute_partisan_lean.py CA"
   ```

### Memory Error in Step 4 or 5
- Increase time or use `savio3_xlmem` partition (if available)
- Reduce number of states processed in parallel if using custom job

### CBG Lookup Not Found
- Ensure Step 1-2 completed successfully
- Check: `ls /global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national.parquet`

---

## Next Steps (After Pipeline Completes)

### 1. Validate Results
```bash
# Check final dataset
R --vanilla << 'EOF'
library(arrow)
df <- read_parquet("/global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean/national_2024/2024-01.parquet")
print(paste("Observations:", nrow(df)))
print(paste("Rep lean range:", round(min(df$rep_lean, na.rm=T), 4), "-", round(max(df$rep_lean, na.rm=T), 4)))
print(paste("Avg coverage:", round(mean(df$pct_visitors_matched, na.rm=T), 2), "%"))
EOF
```

### 2. Review Diagnostic Reports
```bash
# Check coverage metrics
head -20 /global/scratch/users/maxkagan/project_oakland/outputs/diagnostics/data_quality_metrics_by_state.csv
```

### 3. Implement Step 7: R Markdown Report
- Adapt Ohio pilot report to national scope
- Use monthly outputs from Step 5 for analysis
- Incorporate diagnostics from Step 6

---

## Documentation

**Full implementation details**: `/global/home/users/maxkagan/project_oakland/IMPLEMENTATION_STATUS.md`

**Original plan**: `/global/home/users/maxkagan/project_oakland/plans/national_scaleup_2024.md`

---

## Quick Links

- **Script directory**: `/global/home/users/maxkagan/project_oakland/scripts/`
- **Output directory**: `/global/scratch/users/maxkagan/project_oakland/outputs/`
- **Logs directory**: `/global/home/users/maxkagan/project_oakland/logs/national_scaleup/`
- **Project home**: `/global/home/users/maxkagan/project_oakland/`

---

**Ready to run?** Execute: `bash /global/home/users/maxkagan/project_oakland/scripts/submit_national_scaleup.sh`
