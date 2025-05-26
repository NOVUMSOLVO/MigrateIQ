#!/bin/bash

# MigrateIQ Demo Startup Script
# This script starts both the backend API server and frontend proxy for demonstration

echo "🚀 Starting MigrateIQ Demo..."
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Check if required Python packages are installed
echo "📦 Checking dependencies..."
python3 -c "import flask, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required dependencies..."
    pip3 install flask flask-cors requests --break-system-packages
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please install manually:"
        echo "pip3 install flask flask-cors requests"
        exit 1
    fi
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check if ports are available
if check_port 8000; then
    echo "⚠️  Warning: Port 8000 is already in use. Backend server may not start."
fi

if check_port 3000; then
    echo "⚠️  Warning: Port 3000 is already in use. Frontend server may not start."
fi

# Create log directory
mkdir -p logs

echo "🔧 Starting backend API server on port 8000..."
python3 dev_server.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! check_port 8000; then
    echo "❌ Failed to start backend server. Check logs/backend.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend server started successfully (PID: $BACKEND_PID)"

echo "🌐 Starting frontend proxy server on port 3000..."
python3 frontend_proxy.py > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 2

# Check if frontend started successfully
if ! check_port 3000; then
    echo "❌ Failed to start frontend server. Check logs/frontend.log for details."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Frontend server started successfully (PID: $FRONTEND_PID)"

# Save PIDs for cleanup
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 MigrateIQ Demo is now running!"
echo "=================================="
echo "📊 Dashboard:    http://localhost:3000"
echo "🔌 Backend API:  http://localhost:8000"
echo "📝 Logs:         logs/ directory"
echo ""
echo "🎯 Demo Features:"
echo "  • Modern Glass Morphism Dashboard"
echo "  • Real-time Project Management"
echo "  • Data Source Integration"
echo "  • Migration Control & Monitoring"
echo "  • Complete API Functionality"
echo ""
echo "🛑 To stop the demo, run: ./stop_demo.sh"
echo "   Or press Ctrl+C and run: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Try to open browser automatically
if command -v open &> /dev/null; then
    echo "🌐 Opening dashboard in browser..."
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    echo "🌐 Opening dashboard in browser..."
    xdg-open http://localhost:3000
else
    echo "🌐 Please open http://localhost:3000 in your browser"
fi

echo ""
echo "✨ Demo is ready! Press Ctrl+C to stop all services."

# Wait for user interrupt
trap 'echo ""; echo "🛑 Stopping demo servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ Demo stopped successfully."; exit 0' INT

# Keep script running
while true; do
    sleep 1
done
