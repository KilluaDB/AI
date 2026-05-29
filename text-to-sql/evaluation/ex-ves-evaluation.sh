#!/bin/bash

# Run from script directory so relative paths work from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed"
    exit 1
fi

# Create virtual environment if not exists (local to evaluation/, separate from main service)
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies (uses evaluation/requirements.txt)
print_info "Installing dependencies..."
pip install -r requirements.txt --quiet

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║  $1${NC}"
    echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}  ▶  $1${NC}"
}

print_done() {
    echo ""
    echo -e "${GREEN}  ✔  $1${NC}"
}

# PostgreSQL connection (override these or export before running)
export PG_HOST="${PG_HOST:-localhost}"
export PG_PORT="${PG_PORT:-5432}"
export PG_DATABASE="${PG_DATABASE:-BIRD}"
export PG_USER="${PG_USER:-postgres}"
export PG_PASSWORD="${PG_PASSWORD:-postgres}"

num_cpus=1
meta_time_out=30.0
time_out=60
mode_gt="gt"
mode_predict="gpt"

# =================
# Small evaluation
# =================
FOO_PRED="../outputs/foo/predict_test.json"
FOO_GOLD="../data/foo/test_gold.sql"
FOO_DB_ROOT="../data/foo/test_databases/"
FOO_DIFF_JSON="../data/foo/test.json"

if [ -f "$FOO_PRED" ] && [ -f "$FOO_GOLD" ]; then
    print_section "FOO TEST — EX EVALUATION"
    print_step "Running Execution Accuracy..."
    python ./evaluation_bird_ex.py --db_root_path "$FOO_DB_ROOT" \
        --predicted_sql_json_path "$FOO_PRED" \
        --data_mode "test" \
        --ground_truth_sql_path "$FOO_GOLD" \
        --num_cpus $num_cpus \
        --mode_predict $mode_predict \
        --diff_json_path "$FOO_DIFF_JSON" \
        --meta_time_out $meta_time_out
    print_done "EX Evaluation Complete"

    print_section "FOO TEST — VES EVALUATION"
    print_step "Running Valid Efficiency Score..."
    python ./evaluation_bird_ves.py \
        --db_root_path "$FOO_DB_ROOT" \
        --predicted_sql_json_path "$FOO_PRED" \
        --data_mode "test" \
        --ground_truth_sql_path "$FOO_GOLD" \
        --num_cpus $num_cpus --meta_time_out $time_out \
        --mode_gt $mode_gt --mode_predict $mode_predict \
        --diff_json_path "$FOO_DIFF_JSON"
    print_done "VES Evaluation Complete"
else
    echo "Skipping foo test evaluation (missing $FOO_PRED or $FOO_GOLD). Run run.sh first to generate predict_test.json."
    echo ""
fi

# =============================================================================
# Full BIRD dev evaluation
# =============================================================================
# db_root_path="./data/bird/dev_databases/"
# data_mode="dev"
# diff_json_path="./data/bird/dev.json"
# predicted_sql_json_path="./outputs/bird/predict_dev.json"
# ground_truth_sql_path="./data/bird/dev_gold.sql"

# # Require prediction file (generate first with run.sh on BIRD dev)
# if [ ! -f "$predicted_sql_json_path" ]; then
#     echo "Error: Prediction file not found: $predicted_sql_json_path"
#     echo "Run the BIRD dev pipeline first, e.g. uncomment and run the BIRD dev block in run.sh"
#     exit 1
# fi
# if [ ! -f "$ground_truth_sql_path" ]; then
#     echo "Error: Ground truth not found: $ground_truth_sql_path"
#     exit 1
# fi

# # evaluate EX
# echo "Evaluate BIRD EX begin!"
# start_time=$(date +%s)
# python ./evaluation/evaluation_bird_ex.py --db_root_path $db_root_path \
#     --predicted_sql_json_path $predicted_sql_json_path \
#     --data_mode $data_mode \
#     --ground_truth_sql_path $ground_truth_sql_path \
#     --num_cpus $num_cpus \
#     --mode_predict $mode_predict \
#     --diff_json_path $diff_json_path \
#     --meta_time_out $meta_time_out
# echo "Evaluate EX done!"

# # evaluate VES
# echo "Evaluate BIRD VES begin!"
# python ./evaluation/evaluation_bird_ves.py \
#     --db_root_path $db_root_path \
#     --predicted_sql_json_path $predicted_sql_json_path \
#     --data_mode $data_mode \
#     --ground_truth_sql_path $ground_truth_sql_path \
#     --num_cpus $num_cpus --meta_time_out $time_out \
#     --mode_gt $mode_gt --mode_predict $mode_predict \
#     --diff_json_path $diff_json_path
# echo "Evaluate VES done!"
# end_time=$(date +%s)
# elapsed=$(( end_time - start_time ))
# elapsed_minutes=$(( elapsed / 60 ))
# elapsed_seconds=$(( elapsed % 60 ))
# echo "BIRD evaluation finished in ${elapsed_minutes} minutes and ${elapsed_seconds} seconds."