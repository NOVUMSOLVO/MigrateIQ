#!/bin/bash

# MigrateIQ Quick Start Script
# This script starts the Django server with a dynamic port

# Configuration
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$APP_DIR/backend/venv"
PYTHON="$VENV_DIR/bin/python3"
MANAGE="$APP_DIR/backend/manage.py"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Find an available port
find_available_port() {
    for port in $(seq 8000 9000); do
        if ! lsof -i :$port > /dev/null 2>&1; then
            echo $port
            return 0
        fi
    done
    return 1
}

# Find an available port
log_info "Finding an available port..."
PORT=$(find_available_port)
if [ -z "$PORT" ]; then
    log_error "No available ports found in range 8000-9000"
    exit 1
fi
log_info "Using port: $PORT"

# Activate virtual environment if it exists
if [ -d "$VENV_DIR" ]; then
    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    log_warning "Virtual environment not found. Using system Python."
    PYTHON="python3"
fi

# Start Django server
log_info "Starting Django server on port $PORT..."
cd "$APP_DIR/backend"
$PYTHON $MANAGE runserver 0.0.0.0:$PORT
