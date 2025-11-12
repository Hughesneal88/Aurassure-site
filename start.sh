#!/bin/bash

# Aurassure Site Startup Script
# This script starts both the backend and frontend servers

echo "Starting Aurassure Data Download Site..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your Aurassure credentials."
    echo "See .env.example for the required format."
    exit 1
fi

# Start backend
echo "🐍 Starting Flask backend..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "⚛️  Starting React frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers are starting!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend running at: http://localhost:5000"
echo "Frontend running at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
