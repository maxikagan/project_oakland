#!/bin/bash
#SBATCH --job-name=match_brands
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/match_brands_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/match_brands_%j.err

module load anaconda3/2024.02-1-11.4

source ~/.bashrc

cd /global/home/users/maxkagan/project_oakland/scripts/entity_resolution

echo "Starting brand matching at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set"
    exit 1
fi

echo "API key configured (length: ${#OPENAI_API_KEY})"

python -u 03_match_brands_embeddings.py

echo "Completed at $(date)"
