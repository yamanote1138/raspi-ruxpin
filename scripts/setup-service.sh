#!/bin/bash
# Raspi Ruxpin - Systemd Service Setup Script
# This script installs and configures the systemd service for auto-start

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="raspi-ruxpin.service"
SERVICE_FILE="$PROJECT_DIR/$SERVICE_NAME"
SYSTEMD_DIR="/etc/systemd/system"

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

# Print banner
echo "======================================"
echo "  Raspi Ruxpin Service Setup"
echo "======================================"
echo ""

# Check if service file exists in project
if [ ! -f "$SERVICE_FILE" ]; then
    log_error "Service file not found: $SERVICE_FILE"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Get current user
CURRENT_USER=$(whoami)

log_info "Setting up systemd service for user: $CURRENT_USER"
log_info "Project directory: $PROJECT_DIR"

# Create temporary service file with correct paths
TEMP_SERVICE="/tmp/$SERVICE_NAME"

log_info "Configuring service file..."
sed "s|/home/pi/raspi-ruxpin|$PROJECT_DIR|g" "$SERVICE_FILE" > "$TEMP_SERVICE"
sed -i "s|User=pi|User=$CURRENT_USER|g" "$TEMP_SERVICE"
sed -i "s|Group=pi|Group=$CURRENT_USER|g" "$TEMP_SERVICE"

# Show what will be installed
echo ""
echo "Service configuration:"
echo "  User: $CURRENT_USER"
echo "  Directory: $PROJECT_DIR"
echo "  Python: $PROJECT_DIR/.venv/bin/python"
echo ""

# Check if user is in required groups
log_info "Checking group membership..."
NEEDS_GPIO=false
NEEDS_AUDIO=false

if ! groups | grep -q gpio; then
    log_warning "User is not in gpio group"
    NEEDS_GPIO=true
fi

if ! groups | grep -q audio; then
    log_warning "User is not in audio group"
    NEEDS_AUDIO=true
fi

if [ "$NEEDS_GPIO" = true ] || [ "$NEEDS_AUDIO" = true ]; then
    log_info "Adding user to required groups..."

    if [ "$NEEDS_GPIO" = true ]; then
        sudo usermod -a -G gpio $CURRENT_USER
        log_success "Added to gpio group"
    fi

    if [ "$NEEDS_AUDIO" = true ]; then
        sudo usermod -a -G audio $CURRENT_USER
        log_success "Added to audio group"
    fi

    log_warning "You need to log out and back in for group changes to take effect"
    echo ""
    read -p "Press Enter to continue with service installation..."
fi

# Check if service already exists
if systemctl list-unit-files | grep -q "^$SERVICE_NAME"; then
    log_warning "Service already exists"

    # Check if it's running
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Stopping existing service..."
        sudo systemctl stop $SERVICE_NAME
    fi

    log_info "Updating service file..."
else
    log_info "Installing new service..."
fi

# Install service file
sudo cp "$TEMP_SERVICE" "$SYSTEMD_DIR/$SERVICE_NAME"
rm "$TEMP_SERVICE"

# Reload systemd
log_info "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
log_info "Enabling service to start on boot..."
sudo systemctl enable $SERVICE_NAME

# Start service
log_info "Starting service..."
sudo systemctl start $SERVICE_NAME

# Wait for service to start
sleep 2

# Check status
log_info "Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Service is running!"
else
    log_error "Service failed to start"
    echo ""
    echo "Check logs with:"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

# Show status
echo ""
sudo systemctl status $SERVICE_NAME --no-pager || true

echo ""
echo "======================================"
echo "  Service Setup Complete!"
echo "======================================"
echo ""
log_success "Raspi Ruxpin will now start automatically on boot"
echo ""
echo "Useful commands:"
echo "  Status:  ${GREEN}sudo systemctl status $SERVICE_NAME${NC}"
echo "  Stop:    ${GREEN}sudo systemctl stop $SERVICE_NAME${NC}"
echo "  Start:   ${GREEN}sudo systemctl start $SERVICE_NAME${NC}"
echo "  Restart: ${GREEN}sudo systemctl restart $SERVICE_NAME${NC}"
echo "  Disable: ${GREEN}sudo systemctl disable $SERVICE_NAME${NC}"
echo ""
echo "View logs:"
echo "  Recent:     ${GREEN}sudo journalctl -u $SERVICE_NAME -n 50${NC}"
echo "  Follow:     ${GREEN}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo "  Since boot: ${GREEN}sudo journalctl -u $SERVICE_NAME -b${NC}"
echo ""
echo "Access the web interface:"
echo "  ${BLUE}http://$(hostname -I | awk '{print $1}'):8080${NC}"
echo ""
log_success "Setup complete! 🐻"
