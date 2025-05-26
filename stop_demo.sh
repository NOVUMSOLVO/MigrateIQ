#!/bin/bash

# MigrateIQ Demo Stop Script
# This script stops the demo servers and cleans up processes

echo "🛑 Stopping MigrateIQ Demo..."
echo "=============================="

# Function to kill process by PID file
kill_by_pidfile() {
    local pidfile=$1
    local service_name=$2
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔴 Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚡ Force stopping $service_name..."
                kill -9 "$pid"
            fi
            echo "✅ $service_name stopped"
        else
            echo "ℹ️  $service_name was not running"
        fi
        rm -f "$pidfile"
    else
        echo "ℹ️  No PID file found for $service_name"
    fi
}

# Stop services using PID files
if [ -d "logs" ]; then
    kill_by_pidfile "logs/backend.pid" "Backend server"
    kill_by_pidfile "logs/frontend.pid" "Frontend server"
else
    echo "ℹ️  No logs directory found"
fi

# Kill any remaining processes by name/port
echo "🔍 Checking for remaining processes..."

# Kill processes using ports 8000 and 3000
for port in 8000 3000; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "🔴 Stopping process on port $port (PID: $pid)..."
        kill "$pid" 2>/dev/null
        sleep 1
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
        echo "✅ Process on port $port stopped"
    fi
done

# Kill any Python processes running our demo scripts
pkill -f "dev_server.py" 2>/dev/null && echo "✅ Stopped dev_server.py processes"
pkill -f "frontend_proxy.py" 2>/dev/null && echo "✅ Stopped frontend_proxy.py processes"

echo ""
echo "🎉 MigrateIQ Demo stopped successfully!"
echo "======================================"
echo ""
echo "📁 Log files are preserved in logs/ directory"
echo "🚀 To restart the demo, run: ./start_demo.sh"
echo ""
