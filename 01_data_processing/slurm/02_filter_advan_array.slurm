#!/bin/bash
#SBATCH --job-name=filter_advan
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --array=0-66
#SBATCH --output=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/filter_advan_%A_%a.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/01_data_processing/logs/filter_advan_%A_%a.err

# Filter Advan monthly patterns to all US states
# Array job: one task per month (67 months: Jan 2019 - Jul 2024)

echo "Starting filter job at $(date)"
echo "Job ID: $SLURM_JOB_ID, Array Task: $SLURM_ARRAY_TASK_ID"

module load python/3.11

# Month list (0-66 corresponds to Jan 2019 - Jul 2024)
MONTHS=(
    2019-01-01 2019-02-01 2019-03-01 2019-04-01 2019-05-01 2019-06-01
    2019-07-01 2019-08-01 2019-09-01 2019-10-01 2019-11-01 2019-12-01
    2020-01-01 2020-02-01 2020-03-01 2020-04-01 2020-05-01 2020-06-01
    2020-07-01 2020-08-01 2020-09-01 2020-10-01 2020-11-01 2020-12-01
    2021-01-01 2021-02-01 2021-03-01 2021-04-01 2021-05-01 2021-06-01
    2021-07-01 2021-08-01 2021-09-01 2021-10-01 2021-11-01 2021-12-01
    2022-01-01 2022-02-01 2022-03-01 2022-04-01 2022-05-01 2022-06-01
    2022-07-01 2022-08-01 2022-09-01 2022-10-01 2022-11-01 2022-12-01
    2023-01-01 2023-02-01 2023-03-01 2023-04-01 2023-05-01 2023-06-01
    2023-07-01 2023-08-01 2023-09-01 2023-10-01 2023-11-01 2023-12-01
    2024-01-01 2024-02-01 2024-03-01 2024-04-01 2024-05-01 2024-06-01
    2024-07-01
)

MONTH=${MONTHS[$SLURM_ARRAY_TASK_ID]}
echo "Processing month: $MONTH"
echo "------------------------------------------------------------"

INPUT_DIR="/global/scratch/users/maxkagan/advan/monthly_patterns_foot_traffic/dewey_2024_08_27_parquet"
OUTPUT_DIR="/global/scratch/users/maxkagan/project_oakland/intermediate/advan_national_filtered"

cd /global/home/users/maxkagan/project_oakland/01_data_processing/python

python filter_advan_all_states.py \
    --month "$MONTH" \
    --input-dir "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR"

echo "------------------------------------------------------------"
echo "Completed at $(date)"
