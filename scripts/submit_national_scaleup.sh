#!/bin/bash
###############################################################################
# National Scale-Up Pipeline Submission Script
#
# Submits SLURM jobs for Steps 0-7 of the national 2024 scale-up pipeline.
# Handles dependency management between sequential and parallel job steps.
#
# Usage: bash submit_national_scaleup.sh [--skip-step N] [--start-step N]
###############################################################################

set -e  # Exit on error

# Configuration
PROJECT_HOME="/global/home/users/maxkagan/project_oakland"
SCRIPT_DIR="${PROJECT_HOME}/scripts"
LOG_DIR="${PROJECT_HOME}/logs/national_scaleup"

# Create log directory
mkdir -p "${LOG_DIR}"

# Job tracking
declare -A JOB_IDS

# Utility functions
log_job() {
  local step=$1
  local job_id=$2
  local description=$3
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step $step submitted: Job $job_id - $description" | tee -a "${LOG_DIR}/submission.log"
}

###############################################################################
# STEP 0: CBSA Crosswalk Setup (Downloads Census MSA delineations)
###############################################################################
echo "=== STEP 0: CBSA Crosswalk Setup ==="
cat > "${LOG_DIR}/step0_cbsa_crosswalk.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --time=00:30:00
#SBATCH --job-name=step0_cbsa_crosswalk
#SBATCH --output=step0_cbsa_crosswalk.log

cd /global/home/users/maxkagan/project_oakland/scripts
python3 00_setup_cbsa_crosswalk.py
EOF

JOB_ID=$(sbatch --parsable "${LOG_DIR}/step0_cbsa_crosswalk.sh")
JOB_IDS[step0]=$JOB_ID
log_job 0 $JOB_ID "CBSA Crosswalk Setup"

###############################################################################
# STEP 1-2: Election Data Setup (Unzip + Build CBG Lookup)
###############################################################################
echo "=== STEP 1-2: Election Data Setup ==="
cat > "${LOG_DIR}/step1_2_election_setup.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --job-name=step1_2_election_setup
#SBATCH --output=step1_2_election_setup.log
#SBATCH --dependency=singleton

cd /global/home/users/maxkagan/project_oakland/scripts
python3 01_02_election_data_setup.py
EOF

JOB_ID=$(sbatch --parsable --dependency=afterok:${JOB_IDS[step0]} "${LOG_DIR}/step1_2_election_setup.sh")
JOB_IDS[step1_2]=$JOB_ID
log_job 1-2 $JOB_ID "Unzip Election Data + Build National CBG Lookup"

###############################################################################
# STEP 3: Filter Advan Data by State (Array Job)
###############################################################################
echo "=== STEP 3: Filter Advan Data by State ==="
cat > "${LOG_DIR}/step3_filter_advan.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --time=06:00:00
#SBATCH --job-name=step3_filter_advan
#SBATCH --output=step3_filter_advan_%a.log
#SBATCH --array=1-51
#SBATCH --dependency=singleton

# State array mapping (1-51: 50 states + DC)
STATES=(
  "AL" "AK" "AZ" "AR" "CA" "CO" "CT" "DE" "DC" "FL"
  "GA" "HI" "ID" "IL" "IN" "IA" "KS" "KY" "LA" "ME"
  "MD" "MA" "MI" "MN" "MS" "MO" "MT" "NE" "NV" "NH"
  "NJ" "NM" "NY" "NC" "ND" "OH" "OK" "OR" "PA" "RI"
  "SC" "SD" "TN" "TX" "UT" "VT" "VA" "WA" "WV" "WI"
  "WY"
)

STATE=${STATES[$((SLURM_ARRAY_TASK_ID - 1))]}

cd /global/home/users/maxkagan/project_oakland/scripts
python3 03_filter_advan_by_state.py ${STATE}
EOF

JOB_ID=$(sbatch --parsable --dependency=afterok:${JOB_IDS[step1_2]} "${LOG_DIR}/step3_filter_advan.sh")
JOB_IDS[step3]=$JOB_ID
log_job 3 $JOB_ID "Filter Advan Data by State (Array Job: 50 states)"

###############################################################################
# STEP 4: Compute Partisan Lean (Array Job)
###############################################################################
echo "=== STEP 4: Compute Partisan Lean ==="
cat > "${LOG_DIR}/step4_compute_partisan.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --job-name=step4_compute_partisan
#SBATCH --output=step4_compute_partisan_%a.log
#SBATCH --array=1-51
#SBATCH --dependency=singleton

# State array mapping (1-51: 50 states + DC)
STATES=(
  "AL" "AK" "AZ" "AR" "CA" "CO" "CT" "DE" "DC" "FL"
  "GA" "HI" "ID" "IL" "IN" "IA" "KS" "KY" "LA" "ME"
  "MD" "MA" "MI" "MN" "MS" "MO" "MT" "NE" "NV" "NH"
  "NJ" "NM" "NY" "NC" "ND" "OH" "OK" "OR" "PA" "RI"
  "SC" "SD" "TN" "TX" "UT" "VT" "VA" "WA" "WV" "WI"
  "WY"
)

STATE=${STATES[$((SLURM_ARRAY_TASK_ID - 1))]}

cd /global/home/users/maxkagan/project_oakland/scripts
python3 04_compute_partisan_lean.py ${STATE}
EOF

JOB_ID=$(sbatch --parsable --dependency=afterok:${JOB_IDS[step3]} "${LOG_DIR}/step4_compute_partisan.sh")
JOB_IDS[step4]=$JOB_ID
log_job 4 $JOB_ID "Compute Partisan Lean by POI (Array Job: 50 states)"

###############################################################################
# STEP 5: Combine and Partition by Month
###############################################################################
echo "=== STEP 5: Combine and Partition ==="
cat > "${LOG_DIR}/step5_combine_partition.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --job-name=step5_combine_partition
#SBATCH --output=step5_combine_partition.log
#SBATCH --dependency=singleton

cd /global/home/users/maxkagan/project_oakland/scripts
python3 05_combine_and_partition.py
EOF

JOB_ID=$(sbatch --parsable --dependency=afterok:${JOB_IDS[step4]} "${LOG_DIR}/step5_combine_partition.sh")
JOB_IDS[step5]=$JOB_ID
log_job 5 $JOB_ID "Combine States and Partition by Month"

###############################################################################
# STEP 6: Generate Diagnostics
###############################################################################
echo "=== STEP 6: Generate Diagnostics ==="
cat > "${LOG_DIR}/step6_diagnostics.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --job-name=step6_diagnostics
#SBATCH --output=step6_diagnostics.log
#SBATCH --dependency=singleton

cd /global/home/users/maxkagan/project_oakland/scripts
python3 06_generate_diagnostics.py
EOF

JOB_ID=$(sbatch --parsable --dependency=afterok:${JOB_IDS[step5]} "${LOG_DIR}/step6_diagnostics.sh")
JOB_IDS[step6]=$JOB_ID
log_job 6 $JOB_ID "Generate Diagnostic Reports"

###############################################################################
# STEP 7: Brand Heterogeneity Analysis
###############################################################################
echo "=== STEP 7: Brand Heterogeneity Analysis ==="
cat > "${LOG_DIR}/step7_brand_heterogeneity.sh" << 'EOF'
#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --job-name=step7_brand_heterogeneity
#SBATCH --output=step7_brand_heterogeneity.log
#SBATCH --dependency=singleton

cd /global/home/users/maxkagan/project_oakland/scripts
python3 07_brand_heterogeneity.py
EOF

JOB_ID=$(sbatch --parsable --dependency=afterok:${JOB_IDS[step5]} "${LOG_DIR}/step7_brand_heterogeneity.sh")
JOB_IDS[step7]=$JOB_ID
log_job 7 $JOB_ID "Brand Heterogeneity Analysis"

###############################################################################
# Summary
###############################################################################
echo ""
echo "=== Job Submission Summary ==="
echo "All jobs submitted successfully!"
echo ""
echo "Job dependency chain:"
echo "  Step 0 (${JOB_IDS[step0]}): CBSA Crosswalk"
echo "  Step 1-2 (${JOB_IDS[step1_2]}): Election Data Setup (depends on 0)"
echo "  Step 3 (${JOB_IDS[step3]}): Filter Advan by State - 51 jobs (depends on 1-2)"
echo "  Step 4 (${JOB_IDS[step4]}): Compute Partisan Lean - 51 jobs (depends on 3)"
echo "  Step 5 (${JOB_IDS[step5]}): Combine and Partition (depends on 4)"
echo "  Step 6 (${JOB_IDS[step6]}): Generate Diagnostics (depends on 5)"
echo "  Step 7 (${JOB_IDS[step7]}): Brand Heterogeneity Analysis (depends on 5)"
echo ""
echo "To monitor progress:"
echo "  squeue -u maxkagan"
echo ""
echo "To view logs:"
echo "  ls -lh ${LOG_DIR}/"
echo ""
echo "Submission log saved to: ${LOG_DIR}/submission.log"
