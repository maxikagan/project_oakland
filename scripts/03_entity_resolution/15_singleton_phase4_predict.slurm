#!/bin/bash
#SBATCH --job-name=singleton_predict
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/singleton_predict_%j.log

MSA=${1:-columbus_oh}
THRESHOLD=${2:-0.4}

echo "============================================================"
echo "Singleton Matching Phase 4: Predict Matches"
echo "MSA: $MSA"
echo "Threshold: $THRESHOLD"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "============================================================"

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

module load gcc/11.4.0
module load python/3.10.12-gcc-11.4.0

export LD_LIBRARY_PATH=/global/software/rocky-8.x86_64/gcc/linux-rocky8-x86_64/gcc-8.5.0/gcc-11.4.0-nfcdl6bpyabpnhhasfzu6y4ge4kfskvl/lib64:$LD_LIBRARY_PATH

python3 -u scripts/03_entity_resolution/15_singleton_phase4_predict.py --msa "$MSA" --threshold "$THRESHOLD"

echo ""
echo "============================================================"
echo "End time: $(date)"
echo "============================================================"
