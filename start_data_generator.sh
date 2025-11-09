#!/bin/bash

# Start Flink Data Generator
# Generates continuous stream of data changes for CDC demo

echo "================================================================"
echo "  Flink Data Stream Generator"
echo "================================================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker services are running
echo -e "${YELLOW}Checking Docker services...${NC}"
if ! docker ps | grep -q "mysql"; then
    echo "MySQL not running. Starting Docker services..."
    docker-compose up -d
    echo "Waiting 15 seconds for services to start..."
    sleep 15
fi

# Check if Python virtual environment exists
if [ ! -d "cdc_env" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv cdc_env
    source cdc_env/bin/activate
    pip install -r requirements.txt
    pip install pymysql faker
else
    source cdc_env/bin/activate
fi

# Check if dependencies are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
python3 -c "import pymysql, faker" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install pymysql faker
fi

echo
echo "================================================================"
echo -e "${GREEN}Starting Data Stream Generator${NC}"
echo "================================================================"
echo
echo "  This will generate continuous INSERT/UPDATE/DELETE operations"
echo "  Rate: 2 operations per second"
echo "  Distribution: INSERT 50%, UPDATE 30%, DELETE 20%"
echo
echo -e "  ${BLUE}Watch CDC events in Web Dashboard: http://localhost:3000${NC}"
echo
echo "  Press Ctrl+C to stop"
echo "================================================================"
echo

# Run the generator
python3 flink_simple_generator.py
