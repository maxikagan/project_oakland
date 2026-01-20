#!/bin/bash
#SBATCH --job-name=extract_coords_v2
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=04:00:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/slurm/logs/extract_coords_v2_%j.out

module load python/3.11

echo "============================================================"
echo "Coordinate Extraction v2 (Parallelized)"
echo "============================================================"
echo "Started: $(date)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory available: $(free -h | grep Mem | awk '{print $2}')"
echo ""

python3 -u /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/02_partisan_lean/extract_coordinates_v2.py \
    --workers 12 \
    --chunk-size 50

echo ""
echo "Finished: $(date)"
echo ""
echo "Peak memory usage:"
sacct -j $SLURM_JOB_ID --format=MaxRSS -n 2>/dev/null || echo "sacct not available yet"
