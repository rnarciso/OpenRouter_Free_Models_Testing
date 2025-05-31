#!/bin/bash

# OpenRouter Model Testing System - Startup Script
# This script starts the application and provides basic usage instructions

echo "====================================================="
echo "  OpenRouter Model Testing System - Startup Script"
echo "====================================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if required packages are installed
echo "Checking required packages..."
python -c "import flask, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install flask requests
fi

# Check if OpenRouter API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Warning: OPENROUTER_API_KEY environment variable is not set."
    echo "Using default API key for demonstration purposes."
    echo "For production use, please set your own API key:"
    echo "export OPENROUTER_API_KEY=\"your-api-key-here\""
    echo ""
fi

# Start the Flask application
echo "Starting the OpenRouter Model Testing System..."
echo "Press Ctrl+C to stop the application."
echo ""

# Start the application in the background
python app.py > flask_output.log 2>&1 &
APP_PID=$!

# Save the PID to a file for later use
echo $APP_PID > flask_pid.txt

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 3

# Check if the application is running
if ps -p $APP_PID > /dev/null; then
    echo "Application started successfully!"
    echo "Access the application at: http://localhost:5002"
    echo ""
    echo "====================================================="
    echo "  Usage Instructions"
    echo "====================================================="
    echo "1. Open your web browser and navigate to: http://localhost:5002"
    echo "2. Select a model from the dropdown menu"
    echo "3. Click 'Test Selected Model' to test a single model"
    echo "4. Click 'Test All Free Models' to test multiple models"
    echo "5. View the results in the table below"
    echo ""
    echo "Note: Testing all models may take several minutes."
    echo "      The application will show a progress indicator."
    echo ""
    echo "To stop the application, run: kill $(cat flask_pid.txt)"
    echo "====================================================="
else
    echo "Error: Failed to start the application."
    echo "Check flask_output.log for details."
    exit 1
fi