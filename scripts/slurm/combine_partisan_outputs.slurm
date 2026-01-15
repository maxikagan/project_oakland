#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --job-name=combine_partisan
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/national/combine_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/national/combine_%j.err

echo "=========================================="
echo "Combine Partisan Lean Outputs"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start: $(date)"
echo "=========================================="

module load python/3.11.6-gcc-11.4.0

cd /global/home/users/maxkagan/project_oakland/scripts
python3 -u combine_partisan_outputs.py

EXIT_CODE=$?
echo "=========================================="
echo "Exit code: $EXIT_CODE"
echo "End: $(date)"
echo "=========================================="

exit $EXIT_CODE
