#!/bin/bash
#SBATCH --job-name=singleton_bigmem
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3_bigmem
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=06:00:00
#SBATCH --array=1-11
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/singleton_bigmem_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/singleton_bigmem_%A_%a.err

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

source ~/.bashrc

module load gcc/11.4.0
module load python/3.10.12-gcc-11.4.0

export LD_LIBRARY_PATH=/global/software/rocky-8.x86_64/gcc/linux-rocky8-x86_64/gcc-8.5.0/gcc-11.4.0-nfcdl6bpyabpnhhasfzu6y4ge4kfskvl/lib64:$LD_LIBRARY_PATH

pip install --user rapidfuzz scikit-learn --quiet

source /global/home/users/maxkagan/measuring_stakeholder_ideology/.env

MSA_LIST="/global/home/users/maxkagan/measuring_stakeholder_ideology/scripts/03_entity_resolution/msa_lists/failed_large_msas.txt"
MSA=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$MSA_LIST")

if [ -z "$MSA" ]; then
    echo "No MSA found for array task $SLURM_ARRAY_TASK_ID"
    exit 1
fi

echo "Processing MSA: $MSA (task $SLURM_ARRAY_TASK_ID)"
echo "Partition: $SLURM_JOB_PARTITION"
echo "Memory available: savio3_bigmem (~386GB)"
echo "Start: $(date)"

python3 -u scripts/03_entity_resolution/16_singleton_national.py "$MSA"

echo "End: $(date)"
