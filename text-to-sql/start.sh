#!/bin/bash

# Text-to-SQL FastAPI Service Startup Script
# This service generates SQL from natural language questions

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

# Check for .env file
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'

# Local Ollama defaults
# LLM_API_KEY=ollama
# LLM_MODEL=mannix/defog-llama3-sqlcoder-8b
# LLM_API_BASE=http://localhost:11434/v1

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
export $(cat .env | grep -v '^#' | xargs)

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
print_info "Installing dependencies..."
pip install -r requirements.txt --quiet

if [ "$LOCAL_DEV" = "true" ]; then
    print_warning "LOCAL_DEV is enabled! K8s database hostnames will be rerouted to localhost."
fi

# Start the service
print_success "Starting Text-to-SQL service on port ${PORT:-8080}"
print_info "API docs available at: http://localhost:${PORT:-8080}/docs"
echo ""

python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --reload
