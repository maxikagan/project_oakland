#!/bin/bash
#SBATCH --job-name=singleton_phase1
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/singleton_phase1_%j.log
#SBATCH --export=OPENAI_API_KEY

# Phase 1: Compute features for singleton POI matching
# Usage: sbatch 12_singleton_phase1_features.slurm columbus_oh

MSA=${1:-columbus_oh}

echo "============================================================"
echo "Singleton Matching Phase 1: Feature Computation"
echo "MSA: $MSA"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "============================================================"

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

module load anaconda3/2024.02-1-11.4

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set"
    exit 1
fi
echo "API key configured (length: ${#OPENAI_API_KEY})"

python -u scripts/03_entity_resolution/12_singleton_phase1_features.py --msa "$MSA"

echo ""
echo "============================================================"
echo "End time: $(date)"
echo "============================================================"
