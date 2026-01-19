#!/bin/bash
#SBATCH --job-name=extract_norm_visits
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=06:00:00
#SBATCH --array=1-96%50
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/extract_norm_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/extract_norm_%A_%a.err

module load python/3.11

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

FILE_INDEX=$((SLURM_ARRAY_TASK_ID + 2000))
echo "Task ${SLURM_ARRAY_TASK_ID} (file ${FILE_INDEX}) starting at $(date)"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}"

python3 scripts/extract_normalized_visits.py ${FILE_INDEX}

echo "Task ${SLURM_ARRAY_TASK_ID} completed at $(date)"
