#!/bin/bash

###############################################################################
# Territory Dashboard - Quick Deployment Script
#
# This script helps you deploy the Territory Dashboard on an internal server
###############################################################################

set -e  # Exit on error

echo "========================================="
echo "Territory Dashboard Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed.${NC}"
    echo "Please install Docker first:"
    echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    echo "  macOS: brew install docker"
    echo "  Windows: Download from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose is not installed.${NC}"
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo ""

# Create necessary directories
mkdir -p data output

echo "Building Docker image..."
docker-compose build

echo ""
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""

# Ask user for deployment type
echo "Select deployment option:"
echo "1) Start dashboard (foreground)"
echo "2) Start dashboard (background/daemon)"
echo "3) Stop dashboard"
echo "4) View logs"
echo "5) Restart dashboard"
echo ""
read -p "Enter option (1-5): " option

case $option in
    1)
        echo ""
        echo "Starting Territory Dashboard in foreground..."
        echo "Press Ctrl+C to stop"
        echo ""
        docker-compose up
        ;;
    2)
        echo ""
        echo "Starting Territory Dashboard in background..."
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✓ Dashboard started successfully${NC}"
        echo ""
        echo "Access the dashboard at:"
        echo "  Local: http://localhost:8501"
        echo "  Network: http://$(hostname -I | awk '{print $1}'):8501"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        ;;
    3)
        echo ""
        echo "Stopping Territory Dashboard..."
        docker-compose down
        echo -e "${GREEN}✓ Dashboard stopped${NC}"
        ;;
    4)
        echo ""
        echo "Viewing logs (Press Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    5)
        echo ""
        echo "Restarting Territory Dashboard..."
        docker-compose restart
        echo -e "${GREEN}✓ Dashboard restarted${NC}"
        echo ""
        echo "Access at: http://localhost:8501"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
