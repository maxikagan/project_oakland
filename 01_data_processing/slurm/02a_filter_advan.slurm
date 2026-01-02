#!/bin/bash
#SBATCH --job-name=filter_advan
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --array=1-12
#SBATCH --output=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/filter_advan_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/filter_advan_%A_%a.err

# Filter Advan 2023 data to Ohio
# Array job: one task per month (1-12 = Jan-Dec 2023)

echo "Starting at $(date)"
echo "Job ID: $SLURM_JOB_ID, Array Task ID: $SLURM_ARRAY_TASK_ID"

# Load Python module
module load python/3.11

# Map array task ID to month
# Task 1 = January, Task 12 = December
MONTH=$(printf "2023-%02d-01" $SLURM_ARRAY_TASK_ID)
echo "Processing month: $MONTH"

# Run the filter script
python /global/home/users/maxkagan/project_westwood/01_data_processing/python/filter_advan.py \
    --state OH \
    --month "$MONTH" \
    --output-dir /global/scratch/users/maxkagan/project_westwood/intermediate/advan_2023_filtered

echo "Completed at $(date)"
