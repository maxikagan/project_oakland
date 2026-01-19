#!/bin/bash
#SBATCH --job-name=extract_entities
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=01:00:00
#SBATCH --mem=90G
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/extract_entities_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/extract_entities_%j.err

echo "========================================"
echo "Step 1: Extract Unique Entities"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo "========================================"

module load python

python3 /global/home/users/maxkagan/project_oakland/scripts/entity_resolution/01_extract_unique_entities.py

echo "========================================"
echo "End time: $(date)"
echo "========================================"
