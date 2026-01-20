#!/bin/bash
#SBATCH --job-name=hybrid_match
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:45:00
#SBATCH --mem=8G
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/hybrid_match_%j.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/hybrid_match_%j.err

# Task 2.2: Hybrid brand matching (fuzzylink approach)
# Uses text-embedding-3-large + Jaro-Winkler distance

mkdir -p /global/home/users/maxkagan/measuring_stakeholder_ideology/logs

source ~/.bashrc
module load python

cd /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/04_validation

echo "Starting hybrid matching job at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo ""

python 03_hybrid_brand_matching.py

echo ""
echo "Job completed at $(date)"
