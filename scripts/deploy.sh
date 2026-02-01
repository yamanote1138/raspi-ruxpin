#!/bin/bash
#
# Raspi Ruxpin Deployment Script
#
# This script automates the deployment process for Raspberry Pi.
# Run this script on your Raspberry Pi after cloning the repository.
#
# Usage:
#   ./scripts/deploy.sh [--update]
#
# Options:
#   --update    Update an existing installation
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
UPDATE_MODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
if [[ "$1" == "--update" ]]; then
    UPDATE_MODE=true
fi

echo -e "${GREEN}=== Raspi Ruxpin Deployment Script ===${NC}"
echo ""

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi.${NC}"
    echo "This script is designed for Raspberry Pi deployment."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Change to project directory
cd "$PROJECT_DIR"
echo "Working directory: $PROJECT_DIR"
echo ""

if [ "$UPDATE_MODE" = true ]; then
    echo -e "${GREEN}=== Update Mode ===${NC}"
    echo "Stopping service..."
    sudo systemctl stop raspi-ruxpin || true

    echo "Pulling latest changes..."
    git pull

else
    echo -e "${GREEN}=== Fresh Installation ===${NC}"

    # Check if .env exists
    if [[ -f .env ]]; then
        echo -e "${YELLOW}.env file already exists. Skipping...${NC}"
    else
        echo "Creating .env from example..."
        cp .env.example .env
        echo -e "${YELLOW}IMPORTANT: Edit .env and set HARDWARE__USE_MOCK_GPIO=false${NC}"
        echo -e "${YELLOW}           and configure your GPIO pins.${NC}"
        read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit later..."
        nano .env
    fi

    # Install system dependencies
    echo ""
    echo "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        python3-dev \
        espeak \
        alsa-utils \
        libasound2-dev

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo ""
        echo "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
fi

# Python dependencies
echo ""
echo "Installing Python dependencies..."
if [[ ! -d .venv ]]; then
    uv venv
fi

source .venv/bin/activate
uv pip install -e ".[hardware]"

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo ""
    echo -e "${RED}Node.js is not installed.${NC}"
    echo "Install Node.js to build the frontend:"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    echo ""
    echo "Then run this script again with --update flag."
    exit 1
fi

# Build frontend
echo ""
echo "Building frontend..."
cd frontend

if [[ ! -d node_modules ]]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "Building production bundle..."
npm run build

cd ..

# Setup systemd service
if [ "$UPDATE_MODE" = false ]; then
    echo ""
    echo "Setting up systemd service..."

    # Adjust service file paths
    SERVICE_FILE="raspi-ruxpin.service"
    TEMP_SERVICE="/tmp/raspi-ruxpin.service"

    # Replace paths in service file
    sed "s|/home/pi/raspi-ruxpin|$PROJECT_DIR|g" "$SERVICE_FILE" > "$TEMP_SERVICE"
    sed -i "s|User=pi|User=$USER|g" "$TEMP_SERVICE"
    sed -i "s|Group=pi|Group=$USER|g" "$TEMP_SERVICE"

    # Install service
    sudo cp "$TEMP_SERVICE" /etc/systemd/system/raspi-ruxpin.service
    sudo systemctl daemon-reload
    sudo systemctl enable raspi-ruxpin

    rm "$TEMP_SERVICE"
fi

# Start/restart service
echo ""
echo "Starting service..."
sudo systemctl restart raspi-ruxpin

# Wait a moment for service to start
sleep 3

# Check status
echo ""
echo "Checking service status..."
sudo systemctl status raspi-ruxpin --no-pager || true

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "Service status:"
echo "  sudo systemctl status raspi-ruxpin"
echo ""
echo "View logs:"
echo "  sudo journalctl -u raspi-ruxpin -f"
echo ""
echo "Access the web interface:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
echo ""

if [ "$UPDATE_MODE" = false ]; then
    echo -e "${YELLOW}Note: If you see errors, check your .env configuration:${NC}"
    echo "  nano .env"
    echo ""
    echo "Make sure to set:"
    echo "  HARDWARE__USE_MOCK_GPIO=false"
    echo "  (and configure your GPIO pins)"
    echo ""
fi

echo "Enjoy your Raspi Ruxpin!"
