#!/bin/bash
#SBATCH --job-name=parse_cbgs_big
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=06:00:00
#SBATCH --array=0-4
#SBATCH --output=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/parse_cbgs_big_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/parse_cbgs_big_%A_%a.err

# Parse visitor CBGs for largest states using bigmem partition
# Array job: 5 largest states (CA, TX, FL, NY, IL)

echo "Starting parse job at $(date)"
echo "Job ID: $SLURM_JOB_ID, Array Task: $SLURM_ARRAY_TASK_ID"

module load python/3.11

# Largest states by POI count
STATES=(CA TX FL NY IL)

STATE=${STATES[$SLURM_ARRAY_TASK_ID]}
echo "Processing state: $STATE (bigmem)"
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
