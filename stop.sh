#!/bin/bash

# MigrateIQ Stop Script
# This script stops the MigrateIQ application

# Configuration
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$APP_DIR/.pids"

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

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    log_warning "PID file not found. The application may not be running."
    exit 0
fi

# Read PIDs from file
read -r DJANGO_PID CELERY_PID FRONTEND_PID < "$PID_FILE"

# Stop Django server
if [ -n "$DJANGO_PID" ]; then
    log_info "Stopping Django server (PID: $DJANGO_PID)..."
    kill -9 "$DJANGO_PID" 2>/dev/null || true
fi

# Stop Celery worker
if [ -n "$CELERY_PID" ]; then
    log_info "Stopping Celery worker (PID: $CELERY_PID)..."
    kill -9 "$CELERY_PID" 2>/dev/null || true
fi

# Stop frontend server
if [ -n "$FRONTEND_PID" ]; then
    log_info "Stopping frontend server (PID: $FRONTEND_PID)..."
    kill -9 "$FRONTEND_PID" 2>/dev/null || true
fi

# Remove PID file
rm -f "$PID_FILE"

log_info "MigrateIQ has been stopped."
