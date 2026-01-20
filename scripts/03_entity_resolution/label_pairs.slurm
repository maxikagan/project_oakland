#!/bin/bash
#SBATCH --job-name=label_pairs
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --mem=4G
#SBATCH --output=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/label_pairs_%j.out
#SBATCH --error=/global/home/users/maxkagan/measuring_stakeholder_ideology/logs/label_pairs_%j.err

# Label POI-company name pairs for entity resolution training data
# Small job: just reading 1000 rows CSV and applying string matching rules

module load python/3.11

cd /global/home/users/maxkagan/measuring_stakeholder_ideology

echo "Starting label_pairs.py at $(date)"
echo "Running on node: $(hostname)"
echo ""

python scripts/03_entity_resolution/label_pairs.py

echo ""
echo "Completed at $(date)"
