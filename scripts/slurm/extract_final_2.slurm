#!/bin/bash
#SBATCH --job-name=extract_final_2
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=01:00:00
#SBATCH --array=1-2
#SBATCH --exclude=n0046.savio2,n0051.savio2
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/extract_final_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/extract_final_%A_%a.err

module load python/3.11

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

MISSING_FILES=(997 1001)
FILE_INDEX=${MISSING_FILES[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "Final extraction task ${SLURM_ARRAY_TASK_ID}: file index ${FILE_INDEX}"
echo "Node: $(hostname)"
echo "Starting at $(date)"

python3 scripts/extract_normalized_visits.py ${FILE_INDEX}

echo "Completed at $(date)"
