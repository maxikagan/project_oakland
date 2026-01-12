#!/bin/bash
#SBATCH --job-name=cbg_national
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/cbg_national_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/cbg_national_%j.err

# Build national CBG partisan lean lookup from all states

echo "Starting CBG lookup build at $(date)"
echo "Job ID: $SLURM_JOB_ID"

module load python/3.11

cd /global/home/users/maxkagan/project_oakland/01_data_processing/python

python build_cbg_lookup_national.py

echo "Completed at $(date)"
