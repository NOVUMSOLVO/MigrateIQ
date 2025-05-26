#!/bin/bash

# MigrateIQ Restart Script
# This script restarts the MigrateIQ application with a dynamic port configuration

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$APP_DIR/backend/venv"
PYTHON="$VENV_DIR/bin/python3"
PIP="$VENV_DIR/bin/pip"
MANAGE="$APP_DIR/backend/manage.py"
LOG_DIR="$APP_DIR/backend/logs"
FRONTEND_DIR="$APP_DIR/frontend"

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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p "$LOG_DIR"

# Find an available port
log_info "Finding an available port..."
PORT=$(python3 "$APP_DIR/find_port.py" --env-file "$APP_DIR/.env" --backend-env-file "$APP_DIR/backend/.env")
log_info "Using port: $PORT"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install backend dependencies
log_info "Installing backend dependencies..."
$PIP install --upgrade pip
$PIP install -r "$APP_DIR/backend/requirements.txt"

# Apply database migrations
log_info "Applying database migrations..."
cd "$APP_DIR/backend"
$PYTHON $MANAGE migrate

# Start Redis if not running
log_info "Checking Redis..."
if ! command -v redis-cli &> /dev/null || ! redis-cli ping &> /dev/null; then
    log_warning "Redis is not running. Some features may not work properly."
    log_info "You can install Redis with: brew install redis"
    log_info "And start it with: brew services start redis"
else
    log_info "Redis is running."
fi

# Start Celery in the background
log_info "Starting Celery worker..."
cd "$APP_DIR/backend"
$VENV_DIR/bin/celery -A migrateiq worker --loglevel=info > "$LOG_DIR/celery.log" 2>&1 &
CELERY_PID=$!
log_info "Celery worker started with PID: $CELERY_PID"

# Start Django server
log_info "Starting Django server on port $PORT..."
cd "$APP_DIR/backend"
$PYTHON $MANAGE runserver 0.0.0.0:$PORT &
DJANGO_PID=$!
log_info "Django server started with PID: $DJANGO_PID"

# Start frontend development server
log_info "Starting frontend development server..."
cd "$FRONTEND_DIR"
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    log_warning "Frontend package.json not found. Skipping frontend start."
else
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        log_warning "Node.js is not installed. Skipping frontend start."
        log_info "You can install Node.js from: https://nodejs.org/"
    else
        # Install frontend dependencies if node_modules doesn't exist
        if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
            log_info "Installing frontend dependencies..."
            npm install
        fi
        
        # Set environment variables for frontend
        export REACT_APP_API_URL="http://localhost:$PORT/api"
        
        # Start frontend server
        npm start &
        FRONTEND_PID=$!
        log_info "Frontend server started with PID: $FRONTEND_PID"
    fi
fi

# Save PIDs to file for later cleanup
echo "$DJANGO_PID $CELERY_PID $FRONTEND_PID" > "$APP_DIR/.pids"

log_info "MigrateIQ is now running!"
log_info "Backend API: http://localhost:$PORT/api/"
log_info "API Documentation: http://localhost:$PORT/api/docs/"
log_info "Admin Interface: http://localhost:$PORT/admin/"
log_info "Frontend: http://localhost:3000/"
log_info ""
log_info "To stop the application, run: ./stop.sh"

# Keep script running to keep the processes alive
wait
