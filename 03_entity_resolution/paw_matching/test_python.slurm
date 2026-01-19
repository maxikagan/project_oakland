#!/bin/bash
#SBATCH --job-name=test_python
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=/global/home/users/maxkagan/project_oakland/logs/test_python_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_oakland/logs/test_python_%j.err

echo "Starting test at $(date)"
module load python
echo "Module loaded"
which python3
python3 --version
echo "About to run Python"
python3 -u -c "print('Hello from Python', flush=True)"
echo "Python completed at $(date)"
