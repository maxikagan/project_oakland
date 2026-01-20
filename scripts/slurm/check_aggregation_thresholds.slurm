#!/bin/bash
#SBATCH --job-name=check_agg_thresholds
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/slurm/logs/check_agg_thresholds_%j.out

module load python/3.11

python3 /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/diagnostics/check_aggregation_thresholds.py
