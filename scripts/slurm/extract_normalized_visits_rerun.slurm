#!/bin/bash
#SBATCH --job-name=extract_norm_rerun
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=08:00:00
#SBATCH --array=1-33
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/extract_rerun_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/extract_rerun_%A_%a.err

module load python/3.11

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

MISSING_FILES=(40 44 982 983 984 985 986 987 988 989 990 991 992 993 994 995 996 997 998 999 1000 1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 1011 1012)
FILE_INDEX=${MISSING_FILES[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "Rerun task ${SLURM_ARRAY_TASK_ID}: file index ${FILE_INDEX} starting at $(date)"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}"

python3 scripts/extract_normalized_visits.py ${FILE_INDEX}

echo "Task ${SLURM_ARRAY_TASK_ID} completed at $(date)"
