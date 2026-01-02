#!/bin/bash
#SBATCH --job-name=parse_cbgs
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --output=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/parse_cbgs_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/parse_cbgs_%j.err

# Parse visitor_home_cbgs and join with CBG partisan lean
# Processes all 12 months of Ohio 2023 data

echo "Starting at $(date)"
echo "Job ID: $SLURM_JOB_ID"

# Load Python module
module load python/3.11

# Run the parsing script
python /global/home/users/maxkagan/project_westwood/01_data_processing/python/parse_visitor_cbgs.py \
    --state OH \
    --input-dir /global/scratch/users/maxkagan/project_westwood/intermediate/advan_2023_filtered \
    --cbg-lookup /global/scratch/users/maxkagan/project_westwood/inputs/cbg_partisan_lean_ohio.parquet \
    --output /global/scratch/users/maxkagan/project_westwood/outputs/location_partisan_lean/ohio_2023.parquet

echo "Completed at $(date)"
