#!/bin/bash

echo "Setting up MigrateIQ..."
echo "This script will set up both the backend and frontend without starting the servers."
echo ""

# Check if python3 is available
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Neither python3 nor python command is available."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if npm is available
if ! command -v npm &>/dev/null; then
    echo "Error: npm command is not available."
    echo "Please install Node.js and npm, then try again."
    exit 1
fi

# Create a virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv backend/venv

# Activate the virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install --upgrade pip

# Check if requirements.txt exists
if [ ! -f "backend/requirements.txt" ]; then
    # Create requirements.txt
    cat > backend/requirements.txt << EOF
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.0
python-dotenv==1.0.0
pandas==2.1.1
numpy==1.26.0
scikit-learn==1.3.1
sqlalchemy==2.0.22
celery==5.3.4
pytest==7.4.2
black==23.9.1
flake8==6.1.0
EOF
    echo "Created requirements.txt file"
fi

# Install only the core dependencies to avoid disk space issues
pip install django==4.2.7 djangorestframework==3.14.0 django-cors-headers==4.3.0 python-dotenv==1.0.0

# Run migrations
echo "Running migrations..."
cd backend
python manage.py makemigrations
python manage.py migrate
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "Setup complete!"
echo ""
echo "To start the backend server:"
echo "  source backend/venv/bin/activate"
echo "  cd backend"
echo "  python manage.py runserver"
echo ""
echo "To start the frontend server (in a separate terminal):"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "Or use the start.sh script to start both servers at once:"
echo "  ./start.sh"
echo ""
