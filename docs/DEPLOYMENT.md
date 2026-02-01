# Deployment Guide

This guide covers deploying Raspi Ruxpin to a Raspberry Pi for production use.

## Prerequisites

- Raspberry Pi 3 or newer (tested on Pi 4)
- Raspberry Pi OS (Bullseye or newer)
- SSH access to your Pi
- Git installed on Pi
- Internet connection for initial setup

## Hardware Setup

### Required Components

1. **Teddy Ruxpin bear** (vintage animatronic toy)
2. **Raspberry Pi** (3 or newer recommended)
3. **Motor driver** (L293D or similar H-bridge)
4. **Power supply** (5V 3A for Pi + motors)
5. **Speaker** (USB or 3.5mm audio)
6. **Jumper wires** and breadboard

### Wiring Diagram

Connect servos to GPIO pins as configured in your `.env`:

```
Eyes Servo:
├── PWM    → GPIO 21 (default)
├── DIR    → GPIO 16 (default)
└── CDIR   → GPIO 20 (default)

Mouth Servo:
├── PWM    → GPIO 25 (default)
├── DIR    → GPIO 7 (default)
└── CDIR   → GPIO 8 (default)
```

**Important**: These are configurable via environment variables. Adjust based on your wiring.

## Software Installation

### 1. Initial System Setup

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
    git \
    python3-dev \
    espeak \
    alsa-utils \
    libasound2-dev
```

### 2. Install uv (Python Package Manager)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell or add to PATH
source $HOME/.cargo/env
```

### 3. Clone Repository

```bash
# Clone the repo
cd ~
git clone https://github.com/yourusername/raspi-ruxpin.git
cd raspi-ruxpin
```

### 4. Install Python Dependencies

```bash
# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate

# Install with hardware dependencies
uv pip install -e ".[hardware]"
```

**Optional: Install Piper TTS** (recommended for better voice quality)

```bash
uv pip install piper-tts
```

### 5. Install Node.js and Build Frontend

```bash
# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install frontend dependencies
cd frontend
npm install

# Build production frontend
npm run build
cd ..
```

### 6. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit configuration
nano .env
```

**Key settings for Raspberry Pi:**

```bash
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8080

# IMPORTANT: Disable mock GPIO for real hardware
HARDWARE__USE_MOCK_GPIO=false

# Configure your GPIO pins (defaults shown)
HARDWARE__EYES_PWM=21
HARDWARE__EYES_DIR=16
HARDWARE__EYES_CDIR=20
HARDWARE__MOUTH_PWM=25
HARDWARE__MOUTH_DIR=7
HARDWARE__MOUTH_CDIR=8

# Audio settings
AUDIO__START_VOLUME=80
AUDIO__MIXER=PCM

# TTS Engine (espeak or piper)
TTS__ENGINE=espeak
TTS__VOICE=en+m3
TTS__SPEED=125
```

### 7. Test Run

Before setting up as a service, test that everything works:

```bash
# From the raspi-ruxpin directory
source .venv/bin/activate
python -m backend.main
```

Visit `http://your-pi-ip:8080` in a browser. Test:
- Eyes and mouth controls
- Text-to-speech
- Phrase playback
- Volume control

Press `Ctrl+C` to stop when testing is complete.

## Production Deployment

### Create Systemd Service

Create a systemd service file to run Raspi Ruxpin automatically on boot:

```bash
sudo nano /etc/systemd/system/raspi-ruxpin.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Raspi Ruxpin Animatronic Control
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspi-ruxpin
Environment="PATH=/home/pi/raspi-ruxpin/.venv/bin"
ExecStart=/home/pi/raspi-ruxpin/.venv/bin/python -m backend.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable raspi-ruxpin

# Start the service now
sudo systemctl start raspi-ruxpin

# Check status
sudo systemctl status raspi-ruxpin
```

### View Logs

```bash
# View service logs
sudo journalctl -u raspi-ruxpin -f

# View last 100 lines
sudo journalctl -u raspi-ruxpin -n 100
```

### Service Management

```bash
# Stop service
sudo systemctl stop raspi-ruxpin

# Restart service
sudo systemctl restart raspi-ruxpin

# Disable auto-start
sudo systemctl disable raspi-ruxpin
```

## Updates and Maintenance

### Updating the Application

```bash
# Stop the service
sudo systemctl stop raspi-ruxpin

# Navigate to project directory
cd ~/raspi-ruxpin

# Pull latest changes
git pull

# Activate virtual environment
source .venv/bin/activate

# Update Python dependencies
uv pip install -e ".[hardware]"

# Rebuild frontend (if frontend changed)
cd frontend
npm install
npm run build
cd ..

# Restart service
sudo systemctl start raspi-ruxpin
```

### Audio Configuration

**Test audio output:**

```bash
# Test speaker
speaker-test -t wav -c 2

# List audio devices
aplay -l

# Set default audio device (if needed)
sudo raspi-config
# Select: System Options → Audio → Select your output
```

**Adjust volume:**

```bash
# Use alsamixer
alsamixer

# Or set directly
amixer set PCM 80%
```

### GPIO Permissions

If you encounter GPIO permission errors:

```bash
# Add user to gpio group
sudo usermod -a -G gpio pi

# Reboot to apply
sudo reboot
```

## Network Configuration

### Static IP Address (Optional)

For reliable access, set a static IP:

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:

```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Reboot to apply:

```bash
sudo reboot
```

### Access from Other Devices

Once running, access from any device on your network:
- Web UI: `http://your-pi-ip:8080`
- Find your Pi's IP: `hostname -I`

## Troubleshooting

### Service Won't Start

```bash
# Check detailed status
sudo systemctl status raspi-ruxpin -l

# Check logs
sudo journalctl -u raspi-ruxpin -n 50 --no-pager

# Test manually
cd ~/raspi-ruxpin
source .venv/bin/activate
python -m backend.main
```

### GPIO Errors

```bash
# Verify GPIO access
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('GPIO OK')"

# Check permissions
groups | grep gpio
```

### Audio Not Working

```bash
# Check audio devices
aplay -l

# Test audio output
speaker-test -t wav -c 2

# Check ALSA mixer
alsamixer

# Verify audio settings in .env
cat .env | grep AUDIO
```

### WebSocket Connection Issues

- Check firewall: `sudo ufw status`
- Verify port 8080 is not blocked
- Check if service is running: `sudo systemctl status raspi-ruxpin`
- Test from Pi itself: `curl http://localhost:8080/api/health`

### High CPU Usage

If experiencing high CPU usage:

1. Check DEBUG mode is off in `.env`:
   ```bash
   DEBUG=false
   ENVIRONMENT=production
   ```

2. Reduce log level:
   ```bash
   # In web UI: Config → System Logs → Set to WARNING or ERROR
   ```

3. Restart service:
   ```bash
   sudo systemctl restart raspi-ruxpin
   ```

## Performance Optimization

### Reduce Boot Time

```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

### Memory Management

For Pi 3 or systems with limited RAM:

```bash
# Increase swap size
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set: CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Security Recommendations

1. **Change default password:**
   ```bash
   passwd
   ```

2. **Enable SSH key authentication:**
   ```bash
   ssh-keygen
   ssh-copy-id pi@your-pi-ip
   ```

3. **Firewall (optional):**
   ```bash
   sudo apt-get install ufw
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 8080/tcp  # Raspi Ruxpin
   sudo ufw enable
   ```

4. **Keep system updated:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

## Backup and Restore

### Backup Configuration

```bash
# Backup environment and config
cd ~/raspi-ruxpin
tar -czf raspi-ruxpin-config-$(date +%Y%m%d).tar.gz .env config/ sounds/

# Download to your computer
scp pi@your-pi-ip:~/raspi-ruxpin/raspi-ruxpin-config-*.tar.gz .
```

### Restore from Backup

```bash
# Upload backup to Pi
scp raspi-ruxpin-config-*.tar.gz pi@your-pi-ip:~/

# Extract on Pi
cd ~/raspi-ruxpin
tar -xzf ~/raspi-ruxpin-config-*.tar.gz

# Restart service
sudo systemctl restart raspi-ruxpin
```

## Additional Resources

- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Project Issues](https://github.com/yourusername/raspi-ruxpin/issues)

## Support

For issues and questions:
- Check the [Troubleshooting section](#troubleshooting)
- Review logs: `sudo journalctl -u raspi-ruxpin -n 100`
- Open an issue on GitHub with:
  - Description of the problem
  - Log output
  - Hardware configuration
  - Software versions
