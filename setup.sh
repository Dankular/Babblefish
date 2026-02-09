#!/bin/bash
# Babblefish Setup Script
# Quick setup for development environment

set -e  # Exit on error

echo "=================================="
echo "  Babblefish Setup Script"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "\n${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js 20+${NC}"
    exit 1
fi

# Server setup
echo -e "\n${YELLOW}Setting up server...${NC}"
cd server

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Server setup complete${NC}"

cd ..

# Client setup
echo -e "\n${YELLOW}Setting up client...${NC}"
cd client

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "node_modules already exists, skipping npm install"
fi

echo -e "${GREEN}✓ Client setup complete${NC}"

cd ..

# Model download
echo -e "\n${YELLOW}Model setup...${NC}"
echo "Models need to be downloaded (~3GB)"
read -p "Download models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd models
    python download_server_models.py
    cd ..
else
    echo "Skipping model download. Run 'cd models && python download_server_models.py' later."
fi

# Environment file
echo -e "\n${YELLOW}Environment configuration...${NC}"
if [ ! -f "server/.env" ]; then
    echo "Creating .env file from template..."
    cp .env.example server/.env
    echo -e "${GREEN}✓ Created server/.env${NC}"
    echo "You can edit server/.env to customize configuration"
else
    echo ".env already exists"
fi

# Done
echo -e "\n${GREEN}=================================="
echo "  Setup Complete!"
echo "==================================${NC}"
echo ""
echo "To start the server:"
echo "  cd server"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "To start the client (in another terminal):"
echo "  cd client"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
echo "See docs/DEPLOYMENT.md for detailed instructions"
