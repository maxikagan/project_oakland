#!/bin/bash
#SBATCH --job-name=build_cbg_lookup
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/build_cbg_lookup_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/build_cbg_lookup_%j.err

# Build CBG partisan lean lookup table for Ohio pilot
# Uses Main Method (RLCR) 2020 Block Group data

echo "Starting at $(date)"
echo "Job ID: $SLURM_JOB_ID"

# Load Python module
module load python/3.11

# Run the script
python /global/home/users/maxkagan/project_westwood/01_data_processing/python/build_cbg_lookup.py \
    --state OH \
    --output /global/scratch/users/maxkagan/project_westwood/inputs/cbg_partisan_lean_ohio.parquet

echo "Completed at $(date)"
