#!/bin/bash

echo "Starting MigrateIQ..."
echo "This script will start both the backend and frontend services."
echo "Press Ctrl+C to stop the services."
echo ""

# Check if the virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Virtual environment not found. Please run setup_backend.sh first."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Frontend dependencies not found. Please run setup_frontend.sh first."
    exit 1
fi

# Start the backend
echo "Starting backend..."
source backend/venv/bin/activate
cd backend
python manage.py runserver 8001 &
BACKEND_PID=$!
cd ..

# Start the frontend
echo "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Function to handle script termination
function cleanup {
    echo "Stopping services..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Register the cleanup function for when the script is terminated
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Services started. Press Ctrl+C to stop."
while true; do
    sleep 1
done
