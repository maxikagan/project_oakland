#!/bin/bash
#SBATCH --job-name=brand_month_agg
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/slurm/logs/brand_month_agg_%j.out

module load python/3.11

python3 -u /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/02_partisan_lean/aggregate_brand_month.py
