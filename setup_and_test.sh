#!/bin/bash

# MigrateIQ Real-World Readiness Setup and Testing Script
# This script sets up the environment and runs comprehensive tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}${1}${NC}"
    echo -e "${PURPLE}$(printf '=%.0s' {1..60})${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Python dependencies for testing
install_test_dependencies() {
    log_info "Installing Python testing dependencies..."
    
    # Check if pip is available
    if ! command_exists pip; then
        log_error "pip is not available. Please install Python and pip first."
        exit 1
    fi
    
    # Install required packages for testing
    pip install --quiet requests psutil || {
        log_warning "Failed to install some dependencies. Continuing anyway..."
    }
    
    log_success "Test dependencies installed"
}

# Setup environment file
setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.sample" ]; then
            cp .env.sample .env
            log_success "Created .env file from .env.sample"
        else
            log_warning "No .env.sample found. Creating basic .env file..."
            cat > .env << EOF
# Basic environment configuration for testing
DEBUG=True
SECRET_KEY=test-secret-key-for-development-only
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
            log_success "Created basic .env file"
        fi
    else
        log_info ".env file already exists"
    fi
}

# Setup backend
setup_backend() {
    log_header "🔧 SETTING UP BACKEND"
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv || python -m venv venv
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install core dependencies only (to avoid disk space issues)
    log_info "Installing core Django dependencies..."
    pip install --quiet django==4.2.7 djangorestframework==3.14.0 django-cors-headers==4.3.0 python-dotenv==1.0.0 psycopg2-binary==2.9.9 || {
        log_warning "Some dependencies failed to install. Continuing with available packages..."
    }
    
    # Run basic Django checks
    log_info "Running Django system checks..."
    python manage.py check --settings=migrateiq.dev_settings || {
        log_warning "Django checks failed. This may be due to missing dependencies."
    }
    
    # Run migrations
    log_info "Running database migrations..."
    python manage.py migrate --settings=migrateiq.dev_settings || {
        log_warning "Migrations failed. Database may not be properly configured."
    }
    
    cd ..
    log_success "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    log_header "🎨 SETTING UP FRONTEND"
    
    if [ ! -d "frontend" ]; then
        log_warning "Frontend directory not found. Skipping frontend setup."
        return
    fi
    
    cd frontend
    
    # Check if Node.js is available
    if ! command_exists npm; then
        log_warning "npm not found. Skipping frontend setup."
        log_info "To install Node.js, visit: https://nodejs.org/"
        cd ..
        return
    fi
    
    # Install dependencies
    log_info "Installing frontend dependencies..."
    npm install --silent || {
        log_warning "Frontend dependency installation failed. Continuing anyway..."
    }
    
    cd ..
    log_success "Frontend setup completed"
}

# Start services for testing
start_services() {
    log_header "🚀 STARTING SERVICES FOR TESTING"
    
    # Start backend server in background
    log_info "Starting Django development server..."
    cd backend
    source venv/bin/activate
    
    # Start Django server in background
    python manage.py runserver --settings=migrateiq.dev_settings 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    
    cd ..
    
    # Wait a moment for server to start
    sleep 3
    
    # Check if backend is running
    if curl -s http://localhost:8000 > /dev/null; then
        log_success "Backend server started successfully (PID: $BACKEND_PID)"
    else
        log_warning "Backend server may not have started properly"
    fi
    
    # Start frontend if available
    if [ -d "frontend" ] && command_exists npm; then
        log_info "Starting React development server..."
        cd frontend
        npm start > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        cd ..
        
        sleep 5
        log_success "Frontend server started (PID: $FRONTEND_PID)"
    else
        log_info "Skipping frontend server (not available)"
    fi
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    
    # Stop backend
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            log_info "Backend server stopped"
        fi
        rm -f backend.pid
    fi
    
    # Stop frontend
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            log_info "Frontend server stopped"
        fi
        rm -f frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "manage.py runserver" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
}

# Run comprehensive tests
run_tests() {
    log_header "🧪 RUNNING COMPREHENSIVE TESTS"
    
    # Install test dependencies
    install_test_dependencies
    
    # Run the comprehensive test suite
    log_info "Executing real-world readiness tests..."
    python3 test_real_world_readiness.py || {
        log_error "Test execution failed"
        return 1
    }
    
    log_success "Test execution completed"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    stop_services
    
    # Remove log files
    rm -f backend.log frontend.log
    
    log_success "Cleanup completed"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    log_header "🏥 MIGRATEIQ REAL-WORLD READINESS TESTING"
    log_info "Starting comprehensive setup and testing process..."
    
    # Check prerequisites
    if ! command_exists python3 && ! command_exists python; then
        log_error "Python is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    # Setup environment
    setup_environment
    
    # Setup backend
    setup_backend
    
    # Setup frontend
    setup_frontend
    
    # Start services
    start_services
    
    # Wait a moment for services to fully start
    sleep 5
    
    # Run tests
    run_tests
    
    log_header "✅ TESTING COMPLETED"
    log_success "Check test_report.json and test_results.log for detailed results"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MigrateIQ Real-World Readiness Setup and Testing"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --setup-only   Only setup the environment, don't run tests"
        echo "  --test-only    Only run tests (assumes environment is already set up)"
        echo ""
        echo "This script will:"
        echo "  1. Set up the development environment"
        echo "  2. Install necessary dependencies"
        echo "  3. Start the backend and frontend servers"
        echo "  4. Run comprehensive real-world readiness tests"
        echo "  5. Generate detailed test reports"
        ;;
    --setup-only)
        setup_environment
        setup_backend
        setup_frontend
        log_success "Setup completed. Run with --test-only to execute tests."
        ;;
    --test-only)
        start_services
        sleep 5
        run_tests
        ;;
    *)
        main
        ;;
esac
