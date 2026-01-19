#!/bin/bash
#SBATCH --job-name=spend_overlap
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=01:00:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/spend_overlap_%j.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/spend_overlap_%j.err

echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "Working directory: $(pwd)"

module load python/3.11

pip install --user pyarrow pandas --quiet

python3 /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/analyze_spend_overlap.py

exit_code=$?

echo "Job finished at $(date)"
echo "Exit code: $exit_code"

exit $exit_code
