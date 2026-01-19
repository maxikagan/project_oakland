#!/bin/bash
#SBATCH --job-name=test_savio2
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/test_savio2_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/test_savio2_%j.err

echo "Starting test at $(date)"
echo "Node: $(hostname)"
module load anaconda3/2024.02-1-11.4
echo "Anaconda module loaded"
which python
echo "Testing simple Python..."
timeout 30 python --version
echo "Exit code: $?"
echo "Test completed at $(date)"
