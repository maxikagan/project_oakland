#!/bin/bash
#SBATCH --job-name=export_json
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=00:30:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/slurm/logs/export_json_%j.out

module load python/3.11

python3 -u /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/05_descriptive/export_website_json.py
