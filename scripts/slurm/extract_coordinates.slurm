#!/bin/bash
#SBATCH --job-name=extract_coords
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=06:00:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/slurm/logs/extract_coords_%j.out

module load python/3.11

echo "Starting coordinate extraction (6 hour time limit)..."
echo "Memory available: $(free -h | grep Mem | awk '{print $2}')"

python3 -u /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/02_partisan_lean/extract_coordinates.py

echo ""
echo "Job complete."
