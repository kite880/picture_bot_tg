#!/bin/bash
# Start Picture Bot script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Picture Bot - Telegram Bot Launcher${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}\n"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Install/Update dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}\n"

# Check configuration
echo -e "${YELLOW}Checking configuration...${NC}"
python3 check_config.py

# Run the bot
echo -e "${GREEN}Starting Picture Bot...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the bot\n${NC}"

python3 main.py
