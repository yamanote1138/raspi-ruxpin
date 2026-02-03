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
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

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
        log_warning ".env file already exists. Skipping..."
    else
        log_info "Creating .env from Raspberry Pi template..."
        cp .env.example.pi .env
        log_success ".env file created"
        log_warning "IMPORTANT: Verify GPIO pin numbers match your wiring!"
        echo ""
        read -p "Press Enter to review .env now, or Ctrl+C to skip..."
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

# Check GPIO permissions
echo ""
log_info "Checking GPIO permissions..."
if groups | grep -q gpio; then
    log_success "User is in gpio group"
else
    log_warning "User is not in gpio group"
    log_info "Adding user to gpio group..."
    sudo usermod -a -G gpio $USER
    log_success "User added to gpio group"
    log_warning "You need to log out and back in for group changes to take effect"
fi

# Test audio
echo ""
log_info "Testing audio setup..."
if aplay -l >/dev/null 2>&1; then
    log_success "Audio devices found"
    echo ""
    echo "Available audio devices:"
    aplay -l | grep -E "^card"
    echo ""

    # Interactive audio device selection
    if [ "$UPDATE_MODE" = false ]; then
        echo "Would you like to select a specific audio device?"
        echo "(If unsure, press 'n' to use the system default)"
        read -p "Select audio device? (y/N): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Get list of cards
            mapfile -t cards < <(aplay -l | grep -oP "^card \K\d+(?=:)" | sort -u)

            if [ ${#cards[@]} -eq 0 ]; then
                log_warning "No audio cards detected"
            elif [ ${#cards[@]} -eq 1 ]; then
                # Only one card, auto-select it
                SELECTED_CARD="${cards[0]}"
                log_info "Only one card available, selecting card $SELECTED_CARD"

                # Update .env with device selection
                if ! grep -q "^AUDIO__DEVICE=" .env; then
                    echo "" >> .env
                    echo "# Audio Device Selection" >> .env
                    echo "AUDIO__DEVICE=plughw:$SELECTED_CARD,0" >> .env
                    echo "AUDIO__CARD_INDEX=$SELECTED_CARD" >> .env
                else
                    sed -i "s|^AUDIO__DEVICE=.*|AUDIO__DEVICE=plughw:$SELECTED_CARD,0|" .env
                    sed -i "s|^AUDIO__CARD_INDEX=.*|AUDIO__CARD_INDEX=$SELECTED_CARD|" .env
                fi

                log_success "Configured to use audio card $SELECTED_CARD"
            else
                # Multiple cards, let user choose
                echo ""
                echo "Multiple audio cards detected:"
                for i in "${!cards[@]}"; do
                    card="${cards[$i]}"
                    card_info=$(aplay -l | grep "^card $card:" | head -1)
                    echo "  [$i] Card $card: $card_info"
                done
                echo ""

                # Get user selection
                while true; do
                    read -p "Select card number (0-$((${#cards[@]} - 1))): " -r
                    if [[ $REPLY =~ ^[0-9]+$ ]] && [ "$REPLY" -ge 0 ] && [ "$REPLY" -lt "${#cards[@]}" ]; then
                        SELECTED_CARD="${cards[$REPLY]}"
                        break
                    else
                        echo "Invalid selection. Please try again."
                    fi
                done

                # Update .env with device selection
                if ! grep -q "^AUDIO__DEVICE=" .env; then
                    echo "" >> .env
                    echo "# Audio Device Selection" >> .env
                    echo "AUDIO__DEVICE=plughw:$SELECTED_CARD,0" >> .env
                    echo "AUDIO__CARD_INDEX=$SELECTED_CARD" >> .env
                else
                    sed -i "s|^AUDIO__DEVICE=.*|AUDIO__DEVICE=plughw:$SELECTED_CARD,0|" .env
                    sed -i "s|^AUDIO__CARD_INDEX=.*|AUDIO__CARD_INDEX=$SELECTED_CARD|" .env
                fi

                log_success "Configured to use audio card $SELECTED_CARD"
                echo ""
                echo "Testing selected audio device..."
                if speaker-test -D plughw:$SELECTED_CARD,0 -t wav -c 2 -l 1 >/dev/null 2>&1; then
                    log_success "Audio test successful!"
                else
                    log_warning "Audio test failed - you may need to adjust the device manually"
                fi
            fi
        else
            log_info "Using system default audio device"
        fi
    fi
else
    log_warning "No audio devices found or aplay failed"
fi

# Setup systemd service
if [ "$UPDATE_MODE" = false ]; then
    echo ""
    log_info "Setting up systemd service..."

    # Check if service file exists
    SERVICE_FILE="raspi-ruxpin.service"
    if [ ! -f "$SERVICE_FILE" ]; then
        log_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi

    TEMP_SERVICE="/tmp/raspi-ruxpin.service"

    # Replace paths in service file
    sed "s|/home/pi/raspi-ruxpin|$PROJECT_DIR|g" "$SERVICE_FILE" > "$TEMP_SERVICE"
    sed -i "s|User=pi|User=$USER|g" "$TEMP_SERVICE"
    sed -i "s|Group=pi|Group=$USER|g" "$TEMP_SERVICE"

    # Install service
    log_info "Installing service file..."
    sudo cp "$TEMP_SERVICE" /etc/systemd/system/raspi-ruxpin.service

    if [ ! -f /etc/systemd/system/raspi-ruxpin.service ]; then
        log_error "Failed to install service file"
        rm "$TEMP_SERVICE"
        exit 1
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable raspi-ruxpin
    log_success "Service installed and enabled"

    rm "$TEMP_SERVICE"
fi

# Start/restart service
echo ""
# Check if service exists before trying to start it
if systemctl list-unit-files | grep -q "raspi-ruxpin.service"; then
    if [ "$UPDATE_MODE" = true ]; then
        log_info "Restarting service..."
        sudo systemctl restart raspi-ruxpin
    else
        log_info "Starting service..."
        sudo systemctl start raspi-ruxpin
    fi

    # Wait a moment for service to start
    sleep 3

    # Check status
    echo ""
    log_info "Checking service status..."
    if systemctl is-active --quiet raspi-ruxpin; then
        log_success "Service is running!"
        sudo systemctl status raspi-ruxpin --no-pager || true
    else
        log_error "Service failed to start"
        echo ""
        echo "Check logs with:"
        echo "  sudo journalctl -u raspi-ruxpin -n 50"
        exit 1
    fi
else
    log_error "Service not found. Installation may have failed."
    echo "Try running the script again or check for errors above."
    exit 1
fi

echo ""
echo "======================================"
echo "  Deployment Complete!"
echo "======================================"
echo ""
log_success "Raspi Ruxpin service is running!"
echo ""
echo "Service commands:"
echo "  Status:  ${GREEN}sudo systemctl status raspi-ruxpin${NC}"
echo "  Stop:    ${GREEN}sudo systemctl stop raspi-ruxpin${NC}"
echo "  Start:   ${GREEN}sudo systemctl start raspi-ruxpin${NC}"
echo "  Restart: ${GREEN}sudo systemctl restart raspi-ruxpin${NC}"
echo ""
echo "View logs:"
echo "  ${GREEN}sudo journalctl -u raspi-ruxpin -f${NC}"
echo ""
echo "Access the web interface:"
echo "  ${BLUE}http://$(hostname -I | awk '{print $1}'):8080${NC}"
echo ""

if [ "$UPDATE_MODE" = false ]; then
    log_warning "Configuration notes:"
    echo "  - GPIO pin numbers: Edit .env to match your wiring"
    echo "  - Add phrases: config/phrases.json"
    echo "  - Add sounds: sounds/ directory"
    echo ""

    # Check if group change requires logout
    if ! groups | grep -q gpio; then
        log_warning "Group changes detected - please log out and back in"
    fi
fi

log_success "Deployment script finished!"
echo ""
echo "Enjoy your Raspi Ruxpin! 🐻"
