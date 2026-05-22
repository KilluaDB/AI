#!/bin/bash

# Text-to-SQL Evaluation Run Script
# Generates SQL predictions on the configured dataset(s)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- PARSE ARGUMENTS ---
for arg in "$@"; do
    case $arg in
        --local-dev)
        export LOCAL_DEV="true"
        shift
        ;;
    esac
done
# -----------------------

# Change to script directory
cd "$(dirname "$0")"

# Check for .env file (lives in the parent project root, shared with start.sh)
if [ ! -f ../.env ]; then
    print_warning ".env file not found. Creating template..."
    cat > ../.env << 'EOF'

# GPT-4o defaults
LLM_API_KEY=your_github_PAT_here
LLM_MODEL=gpt-4o
LLM_API_BASE=https://models.github.ai/inference

# Service Port
PORT=8080
EOF
    print_info "Created .env template"
    print_info "The service will use api_config.py defaults unless you override in .env"
    print_info "Current api_config.py settings will be used for LLM configuration"
fi

# Load environment variables
export $(cat ../.env | grep -v '^#' | xargs)

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

# PostgreSQL connection settings (used when --use_postgres is passed)
export PG_HOST="${PG_HOST:-localhost}"
export PG_PORT="${PG_PORT:-5432}"
export PG_DATABASE="${PG_DATABASE:-BIRD}"
export PG_USER="${PG_USER:-postgres}"
export PG_PASSWORD="${PG_PASSWORD:-postgres}"

# Generate SQL on foo dataset for env test (PostgreSQL mode)
# This will get ./outputs/foo/output_bird.json and ./outputs/foo/predict_test.json
#===============================================#
print_info "Starting Foo dataset prediction (PostgreSQL)..."
start_time=$(date +%s)
python ./run.py --dataset_name "bird" \
   --dataset_mode="test" \
   --input_file "../data/foo/test.json" \
   --output_file "../outputs/foo/output_bird.json" \
   --log_file "../outputs/foo/log.txt" \
   --use_postgres
end_time=$(date +%s)
elapsed=$(( end_time - start_time ))
elapsed_minutes=$(( elapsed / 60 ))
elapsed_seconds=$(( elapsed % 60 ))
print_success "BIRD dev prediction finished in ${elapsed_minutes} minutes and ${elapsed_seconds} seconds."


# #################### BIRD dev 【run】count=1534 #########
# Generate SQL on BIRD dev dataset (with timing)
#===============================================#
# echo "Starting BIRD dev prediction..."
# start_time=$(date +%s)
# python ./run.py --dataset_name="bird" \
#    --dataset_mode="dev" \
#    --input_file="./data/bird/dev.json" \
#    --db_path="./data/bird/dev_databases/" \
#    --tables_json_path "./data/bird/dev_tables.json" \
#    --output_file="./outputs/bird/output_bird.json" \
#    --log_file="./outputs/bird/log.txt"
# end_time=$(date +%s)
# elapsed=$(( end_time - start_time ))
# elapsed_minutes=$(( elapsed / 60 ))
# elapsed_seconds=$(( elapsed % 60 ))
# echo "BIRD dev prediction finished in ${elapsed_minutes} minutes and ${elapsed_seconds} seconds."


# use gold schema
#===============================================#
# python ./run.py --dataset_name="bird" \
#    --dataset_mode="dev" \
#    --input_file="./data/bird/dev.json" \
#    --db_path="./data/bird/dev_databases/" \
#    --tables_json_path "./data/bird/dev_tables.json" \
#    --output_file="./outputs/bird_gold_schema/output_bird.json" \
#    --log_file="./outputs/bird_gold_schema/log.txt" \
#    --use_gold_schema


# #################### BIRD dev 【evaluation】=1534, see evaluation_bird_ex_ves.sh #########

print_success "Done!"
