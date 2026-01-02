#!/bin/bash
#SBATCH --job-name=unzip_ohio
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/unzip_ohio_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_westwood/01_data_processing/logs/unzip_ohio_%j.err

# Unzip Ohio election data for Project Westwood pilot
# Ohio FIPS code: 39 -> file is "390 OH.zip"

echo "Starting unzip at $(date)"
echo "Job ID: $SLURM_JOB_ID"

INPUT_FILE="/global/scratch/users/maxkagan/election_results_geocoded/390 OH.zip"
OUTPUT_DIR="/global/scratch/users/maxkagan/project_westwood/inputs/election_data_raw"

# Unzip Ohio election data
unzip -o "$INPUT_FILE" -d "$OUTPUT_DIR"

echo "Completed at $(date)"
echo "Contents of output directory:"
ls -la "$OUTPUT_DIR"
