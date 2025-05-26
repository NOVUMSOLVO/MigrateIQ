#!/bin/bash

# MigrateIQ Deployment Script
# This script deploys the MigrateIQ application to a production environment

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$APP_DIR/backend/venv"
PYTHON="$VENV_DIR/bin/python3"
PIP="$VENV_DIR/bin/pip"
MANAGE="$APP_DIR/backend/manage.py"
LOG_DIR="$APP_DIR/backend/logs"
STATIC_DIR="$APP_DIR/backend/staticfiles"
FRONTEND_DIR="$APP_DIR/frontend"
FRONTEND_BUILD_DIR="$FRONTEND_DIR/build"

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

# Check if .env file exists
if [ ! -f "$APP_DIR/backend/.env" ]; then
    log_error "No .env file found in backend directory!"
    log_info "Creating .env file from .env.sample..."
    
    if [ -f "$APP_DIR/backend/.env.sample" ]; then
        cp "$APP_DIR/backend/.env.sample" "$APP_DIR/backend/.env"
        log_warning "Please update the .env file with your production settings!"
    else
        log_error ".env.sample file not found. Please create a .env file manually."
        exit 1
    fi
fi

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p "$LOG_DIR"
mkdir -p "$STATIC_DIR"

# Update backend dependencies
log_info "Updating backend dependencies..."
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
$PIP install --upgrade pip
$PIP install -r "$APP_DIR/backend/requirements.txt"

# Apply database migrations
log_info "Applying database migrations..."
$PYTHON $MANAGE migrate

# Collect static files
log_info "Collecting static files..."
$PYTHON $MANAGE collectstatic --noinput

# Build frontend
log_info "Building frontend..."
cd "$FRONTEND_DIR"
npm install
npm run build

# Copy frontend build to static directory
log_info "Copying frontend build to static directory..."
cp -r "$FRONTEND_BUILD_DIR"/* "$STATIC_DIR"

# Create or update supervisor configuration
log_info "Setting up process management..."
SUPERVISOR_CONF="/tmp/migrateiq_supervisor.conf"

cat > "$SUPERVISOR_CONF" << EOF
[program:migrateiq_gunicorn]
command=$VENV_DIR/bin/gunicorn migrateiq.wsgi:application --workers 4 --bind 0.0.0.0:8000
directory=$APP_DIR/backend
user=$(whoami)
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/gunicorn.log
stderr_logfile=$LOG_DIR/gunicorn_error.log

[program:migrateiq_celery]
command=$VENV_DIR/bin/celery -A migrateiq worker --loglevel=info
directory=$APP_DIR/backend
user=$(whoami)
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/celery.log
stderr_logfile=$LOG_DIR/celery_error.log

[group:migrateiq]
programs=migrateiq_gunicorn,migrateiq_celery
EOF

log_info "Supervisor configuration created at $SUPERVISOR_CONF"
log_info "To install the supervisor configuration, run:"
log_info "sudo cp $SUPERVISOR_CONF /etc/supervisor/conf.d/migrateiq.conf"
log_info "sudo supervisorctl reread"
log_info "sudo supervisorctl update"

# Final instructions
log_info "Deployment completed successfully!"
log_info "To start the application manually:"
log_info "1. Start the Django server: $VENV_DIR/bin/gunicorn migrateiq.wsgi:application --workers 4 --bind 0.0.0.0:8000"
log_info "2. Start Celery worker: $VENV_DIR/bin/celery -A migrateiq worker --loglevel=info"
log_info ""
log_info "For production deployment, consider using Supervisor or systemd to manage these processes."
