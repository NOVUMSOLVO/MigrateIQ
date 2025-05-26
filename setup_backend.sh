#!/bin/bash

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

# Create a virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv backend/venv

# Activate the virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Run migrations
echo "Running migrations..."
cd backend
python manage.py makemigrations
python manage.py migrate

# Create a superuser
echo "Creating a superuser..."
python manage.py createsuperuser

# Run the server
echo "Starting the server..."
python manage.py runserver
