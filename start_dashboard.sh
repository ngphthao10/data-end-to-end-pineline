#!/bin/bash

# Start CDC Web Dashboard
# This script starts both Flask backend and Next.js frontend

echo "================================================================"
echo "  Starting CDC Web Dashboard"
echo "================================================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
echo -e "${YELLOW}Checking Docker services...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo "Docker services not running. Starting..."
    docker-compose up -d
    sleep 10
fi

# Start Flask backend
echo -e "${GREEN}Starting Flask backend...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start Flask in background
python app.py &
FLASK_PID=$!
echo "Flask backend started (PID: $FLASK_PID) on http://localhost:5000"

cd ..

# Start Next.js frontend
echo -e "${GREEN}Starting Next.js frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

# Start Next.js in foreground
npm run dev &
NEXTJS_PID=$!
echo "Next.js frontend started (PID: $NEXTJS_PID) on http://localhost:3000"

echo
echo "================================================================"
echo -e "${GREEN}Dashboard is starting!${NC}"
echo "================================================================"
echo
echo "  Backend:  http://localhost:5000"
echo "  Frontend: http://localhost:3000"
echo
echo "  Opening browser in 5 seconds..."
echo
echo "  Press Ctrl+C to stop all services"
echo "================================================================"

# Wait a bit then open browser
sleep 5
open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

# Wait for user to stop
wait
