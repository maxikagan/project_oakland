#!/bin/bash
#SBATCH --job-name=filter_us_pois
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=01:00:00
#SBATCH --mem=90G
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/filter_us_pois_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/filter_us_pois_%j.err

echo "========================================"
echo "Step 0: Filter Advan POIs to US-only"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo "========================================"

module load python

pip install --user duckdb --quiet

python3 /global/home/users/maxkagan/project_oakland/scripts/entity_resolution/00_filter_us_pois.py

echo "========================================"
echo "End time: $(date)"
echo "========================================"
