#!/bin/bash
#SBATCH --job-name=schoen_match
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:20:00
#SBATCH --mem=4G
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/schoen_match_%j.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/schoen_match_%j.err

# Task 2.2: Match Schoenmueller brands to Advan brands using semantic similarity

mkdir -p /global/home/users/maxkagan/measuring_stakeholder_ideology/logs

source ~/.bashrc
module load python

cd /global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/04_validation

echo "Starting brand matching job at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo ""

python 02_match_schoenmueller_brands.py

echo ""
echo "Job completed at $(date)"
