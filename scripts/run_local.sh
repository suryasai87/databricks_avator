#!/bin/bash

# Run Databricks Avatar Assistant Locally
# This allows fast local development without Databricks costs

set -e

echo "========================================="
echo "Databricks Avatar Assistant - Local Mode"
echo "========================================="

# Check if we're in the project root
if [ ! -f "databricks.yml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your credentials"
fi

# Load environment variables
export $(cat .env | grep -v '#' | xargs)

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt --quiet
cd ..

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

# Start backend in background
echo ""
echo "Starting backend server on http://localhost:8000..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo ""
echo "Starting frontend on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================="
echo "Application running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
