#!/bin/bash
#SBATCH --job-name=parse_cbgs
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --array=0-45
#SBATCH --output=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/parse_cbgs_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/parse_cbgs_%A_%a.err

# Parse visitor CBGs and calculate partisan lean for each state
# Array job: 46 states (excludes CA, TX, FL, NY, IL which use bigmem)

echo "Starting parse job at $(date)"
echo "Job ID: $SLURM_JOB_ID, Array Task: $SLURM_ARRAY_TASK_ID"

module load python/3.11

# State list (excludes CA, TX, FL, NY, IL - handled by bigmem job)
STATES=(
    AL AK AZ AR CO CT DE DC
    GA HI ID IN IA KS KY LA ME
    MD MA MI MN MS MO MT NE NV NH
    NJ NM NC ND OH OK OR PA RI
    SC SD TN UT VT VA WA WV WI WY
)

STATE=${STATES[$SLURM_ARRAY_TASK_ID]}
echo "Processing state: $STATE"
echo "------------------------------------------------------------"

INPUT_DIR="/global/scratch/users/maxkagan/project_oakland/intermediate/advan_national_filtered/parquet"
CBG_LOOKUP="/global/scratch/users/maxkagan/project_oakland/inputs/cbg_partisan_lean_national.parquet"
OUTPUT_DIR="/global/scratch/users/maxkagan/project_oakland/outputs/location_partisan_lean"

cd /global/home/users/maxkagan/project_oakland/01_data_processing/python

python parse_visitor_cbgs_national.py \
    --state "$STATE" \
    --input-dir "$INPUT_DIR" \
    --cbg-lookup "$CBG_LOOKUP" \
    --output-dir "$OUTPUT_DIR"

echo "------------------------------------------------------------"
echo "Completed at $(date)"
