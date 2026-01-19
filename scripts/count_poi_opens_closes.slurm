#!/bin/bash
#SBATCH --job-name=poi_lifecycle
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/poi_lifecycle_%j.log
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/poi_lifecycle_%j.err

module load python/3.11

cd /global/home/users/maxkagan/project_oakland

python -u scripts/count_poi_opens_closes.py
