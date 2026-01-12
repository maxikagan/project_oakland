#!/bin/bash
#SBATCH --job-name=unzip_election
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --array=0-50
#SBATCH --output=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/unzip_election_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/unzip_election_%A_%a.err

# Unzip all election data for Project Oakland
# Uses SLURM array to process each zip file in parallel

echo "Starting unzip at $(date)"
echo "Job ID: $SLURM_JOB_ID, Array Task ID: $SLURM_ARRAY_TASK_ID"

INPUT_DIR="/global/scratch/users/maxkagan/election_results_geocoded"
OUTPUT_DIR="/global/scratch/users/maxkagan/project_oakland/inputs/election_data_raw"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get list of all zip files (excluding Contiguous USA aggregates)
mapfile -t ZIP_FILES < <(ls "$INPUT_DIR"/*.zip | grep -v "Contiguous USA")

# Get the file for this array task
if [ $SLURM_ARRAY_TASK_ID -ge ${#ZIP_FILES[@]} ]; then
    echo "No file for task ID $SLURM_ARRAY_TASK_ID (only ${#ZIP_FILES[@]} files)"
    exit 0
fi

ZIP_FILE="${ZIP_FILES[$SLURM_ARRAY_TASK_ID]}"
echo "Processing: $ZIP_FILE"

# Unzip
unzip -o "$ZIP_FILE" -d "$OUTPUT_DIR"

echo "Completed at $(date)"
