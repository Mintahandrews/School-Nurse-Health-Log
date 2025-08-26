#!/bin/bash

# Run the School Nurse Health Log Web App
echo "Starting School Nurse Health Log Web App..."
echo "The app will be available at: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop the server"
echo "---------------------------------------------"

# Create instance directory if it doesn't exist
mkdir -p instance

# Set development environment
export FLASK_CONFIG=development

# Run the Flask app using the new entry point
python3 run.py
