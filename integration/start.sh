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

# Change to script directory
cd "$(dirname "$0")"

# Check for .env file
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'
# LLM Configuration (Optional - defaults to api_config.py if not set)
# Uncomment and set these to override api_config.py settings:

# LLM_API_KEY=ollama
# LLM_MODEL=mannix/defog-llama3-sqlcoder-8b
# LLM_API_BASE=http://localhost:11434/v1

# Local Ollama defaults
LLM_API_KEY=ollama
LLM_MODEL=mannix/defog-llama3-sqlcoder-8b
LLM_API_BASE=http://localhost:11434/v1

# Service Port
PORT=5001
EOF
    print_info "Created .env template"
    print_info "The service will use api_config.py defaults unless you override in .env"
    print_info "Current api_config.py settings will be used for LLM configuration"
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check local Ollama defaults
if [ -z "${LLM_API_KEY:-}" ]; then
    export LLM_API_KEY="ollama"
    print_info "LLM_API_KEY not set, defaulting to 'ollama'"
fi
if [ -z "${LLM_MODEL:-}" ]; then
    export LLM_MODEL="mannix/defog-llama3-sqlcoder-8b"
    print_info "LLM_MODEL not set, defaulting to 'mannix/defog-llama3-sqlcoder-8b'"
fi
if [ -z "${LLM_API_BASE:-}" ]; then
    export LLM_API_BASE="http://localhost:11434/v1"
    print_info "LLM_API_BASE not set, defaulting to Ollama local endpoint"
fi

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

# Start the service
print_success "Starting Text-to-SQL service on port ${PORT:-5001}"
print_info "API docs available at: http://localhost:${PORT:-5001}/docs"
echo ""

uvicorn main:app --host 0.0.0.0 --port ${PORT:-5001} --reload
