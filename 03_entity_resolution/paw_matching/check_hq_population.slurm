#!/bin/bash
#SBATCH --job-name=check_hq_pop
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --mem=32G
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/check_hq_pop_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/check_hq_pop_%j.err

echo "========================================"
echo "HQ Metro Population Check"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo "========================================"

module load python

python3 /global/home/users/maxkagan/project_oakland/scripts/entity_resolution/check_hq_population.py

echo "========================================"
echo "End time: $(date)"
echo "========================================"
