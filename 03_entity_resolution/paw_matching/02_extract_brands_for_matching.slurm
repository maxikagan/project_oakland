#!/bin/bash
#SBATCH --job-name=extract_brands
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --time=00:30:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/extract_brands_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/extract_brands_%j.err

module load anaconda3/2024.02-1-11.4

cd /global/home/users/maxkagan/project_oakland/scripts/entity_resolution

echo "Starting brand extraction at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"

python -u 02_extract_brands_for_matching.py

echo "Completed at $(date)"
