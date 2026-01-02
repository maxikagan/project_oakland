#!/bin/bash
#SBATCH --job-name=ohio_analysis
#SBATCH --account=fc_basicperms
#SBATCH --partition=savio2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --mem=32G
#SBATCH --output=/global/home/users/maxkagan/project_westwood/02_descriptive_analysis/logs/render_%j.out
#SBATCH --error=/global/home/users/maxkagan/project_westwood/02_descriptive_analysis/logs/render_%j.err

echo "Starting at $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Running on node: $(hostname)"

# Load R module
module load r/4.4.0

# Set paths
RMD_FILE="/global/home/users/maxkagan/project_westwood/02_descriptive_analysis/rmd/ohio_2023_analysis.Rmd"
OUTPUT_DIR="/global/home/users/maxkagan/project_westwood/02_descriptive_analysis/output"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Install required packages if not present (to user library)
Rscript -e "
packages <- c('arrow', 'dplyr', 'ggplot2', 'tidyr', 'scales', 'knitr', 'kableExtra', 'ggridges', 'rmarkdown')
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg, repos = 'https://cloud.r-project.org/', quiet = TRUE)
  }
}
"

echo "Rendering R Markdown..."

# Render to HTML
Rscript -e "rmarkdown::render('$RMD_FILE', output_dir = '$OUTPUT_DIR', output_format = 'html_document')"

# Check if rendering succeeded
if [ -f "$OUTPUT_DIR/ohio_2023_analysis.html" ]; then
    echo "SUCCESS: HTML report created at $OUTPUT_DIR/ohio_2023_analysis.html"
    ls -la "$OUTPUT_DIR"
else
    echo "ERROR: HTML report was not created"
    exit 1
fi

echo "Completed at $(date)"
