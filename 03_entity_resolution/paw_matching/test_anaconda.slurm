#!/bin/bash
#SBATCH --job-name=test_anaconda
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/test_anaconda_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/test_anaconda_%j.err

echo "Starting test at $(date)"
module load anaconda3/2024.02-1-11.4
echo "Anaconda module loaded"
which python
echo "About to run python --version"
python --version
echo "About to run Python script"
python -u -c "print('Hello from Anaconda Python', flush=True)"
echo "Testing duckdb import"
python -u -c "import duckdb; print('DuckDB version:', duckdb.__version__)"
echo "Python completed at $(date)"
