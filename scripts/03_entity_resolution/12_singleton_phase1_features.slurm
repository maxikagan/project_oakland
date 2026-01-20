#!/bin/bash
#SBATCH --job-name=singleton_phase1
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
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

module load gcc/11.4.0
module load python/3.10.12-gcc-11.4.0

# Set library path for gcc 11.4.0 runtime libraries
export LD_LIBRARY_PATH=/global/software/rocky-8.x86_64/gcc/linux-rocky8-x86_64/gcc-8.5.0/gcc-11.4.0-nfcdl6bpyabpnhhasfzu6y4ge4kfskvl/lib64:$LD_LIBRARY_PATH

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set"
    exit 1
fi
echo "API key configured (length: ${#OPENAI_API_KEY})"

python3 -u scripts/03_entity_resolution/12_singleton_phase1_features.py --msa "$MSA"

echo ""
echo "============================================================"
echo "End time: $(date)"
echo "============================================================"
