#!/bin/bash
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --time=02:00:00
#SBATCH --job-name=partisan_lean
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/national/partisan_%a_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/national/partisan_%a_%j.err
#SBATCH --array=1-1000%50

echo "=========================================="
echo "Partisan Lean Computation"
echo "Task: $SLURM_ARRAY_TASK_ID / 2096"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start: $(date)"
echo "=========================================="

module load python/3.11.6-gcc-11.4.0

cd /global/home/users/maxkagan/project_oakland/scripts
python3 -u compute_partisan_lean_direct.py $SLURM_ARRAY_TASK_ID

EXIT_CODE=$?
echo "=========================================="
echo "Exit code: $EXIT_CODE"
echo "End: $(date)"
echo "=========================================="

exit $EXIT_CODE
