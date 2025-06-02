#!/bin/bash

# Stop any existing Flask app
if [ -f flask_pid.txt ]; then
    kill $(cat flask_pid.txt) 2>/dev/null
    rm flask_pid.txt
    echo "Stopped existing Flask app"
fi

# Start the application
./start_app.sh