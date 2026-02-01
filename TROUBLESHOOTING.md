# Raspi Ruxpin Troubleshooting Guide

This guide covers common issues you might encounter when running Raspi Ruxpin on Raspberry Pi hardware.

## Table of Contents

- [Service Won't Start](#service-wont-start)
- [GPIO Issues](#gpio-issues)
- [Audio Problems](#audio-problems)
- [Servo Issues](#servo-issues)
- [WebSocket Connection Issues](#websocket-connection-issues)
- [Performance Issues](#performance-issues)
- [Development Issues](#development-issues)

---

## Service Won't Start

### Symptom: Service fails immediately after starting

**Check service status:**
```bash
sudo systemctl status raspi-ruxpin
```

**View recent logs:**
```bash
sudo journalctl -u raspi-ruxpin -n 100 --no-pager
```

### Common Causes:

#### 1. Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'fastapi'` or similar

**Solution:**
```bash
cd /home/pi/raspi-ruxpin
source .venv/bin/activate
uv pip install -e ".[hardware]"
sudo systemctl restart raspi-ruxpin
```

#### 2. Wrong Python Path

**Error:** `python: No such file or directory`

**Solution:**
Check that virtual environment exists:
```bash
ls -la /home/pi/raspi-ruxpin/.venv/bin/python
```

If missing, recreate:
```bash
cd /home/pi/raspi-ruxpin
uv venv
source .venv/bin/activate
uv pip install -e ".[hardware]"
```

#### 3. Invalid .env Configuration

**Error:** `ValidationError` in logs

**Solution:**
Verify `.env` file exists and has correct syntax:
```bash
cat .env
```

Reset from template:
```bash
cp .env.example.pi .env
nano .env  # Edit as needed
```

#### 4. Frontend Not Built

**Error:** `404` errors in logs for static files

**Solution:**
Build frontend:
```bash
cd /home/pi/raspi-ruxpin/frontend
npm run build
cd ..
sudo systemctl restart raspi-ruxpin
```

---

## GPIO Issues

### Symptom: "GPIO not initialized" or "Failed to initialize GPIO"

#### 1. Mock GPIO Still Enabled

**Check `.env` file:**
```bash
grep MOCK_GPIO .env
```

**Should show:**
```bash
HARDWARE__USE_MOCK_GPIO=false
```

**If wrong, fix it:**
```bash
nano .env
# Change to: HARDWARE__USE_MOCK_GPIO=false
sudo systemctl restart raspi-ruxpin
```

#### 2. Permission Denied

**Error:** `RuntimeError: No access to /dev/gpiomem`

**Solution:**
Add user to gpio group:
```bash
sudo usermod -a -G gpio pi
# Log out and back in, then:
sudo systemctl restart raspi-ruxpin
```

**Verify group membership:**
```bash
groups
# Should include: gpio
```

#### 3. RPi.GPIO Not Installed

**Error:** `ModuleNotFoundError: No module named 'RPi'`

**Solution:**
```bash
cd /home/pi/raspi-ruxpin
source .venv/bin/activate
uv pip install RPi.GPIO
sudo systemctl restart raspi-ruxpin
```

### Symptom: GPIO Status Panel Shows Wrong States

**Check in System view** - GPIO pins should reflect actual hardware state.

**If all pins show LOW:**
- GPIO might not be initialized
- Check logs: `sudo journalctl -u raspi-ruxpin -f`

**If pins don't update:**
- WebSocket might be disconnected
- Refresh browser
- Check connection status indicator

---

## Audio Problems

### Symptom: No sound output

#### 1. Check Audio Devices

**List available devices:**
```bash
aplay -l
```

**Should show at least one device:**
```
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
```

**If no devices:**
- Check hardware connections
- Enable audio in `raspi-config`

#### 2. Check Volume Level

**Test speaker:**
```bash
speaker-test -t wav -c 2
# Press Ctrl+C to stop
```

**Adjust volume:**
```bash
alsamixer
# Use arrow keys, F6 to select card
```

**Or set via command:**
```bash
amixer set PCM 100%
```

#### 3. Wrong Audio Mixer

**Check `.env` file:**
```bash
grep AUDIO__MIXER .env
```

**Try different mixers:**
- `PCM` (most common)
- `Master`
- `Speaker`

**Test which mixers are available:**
```bash
amixer scontrols
```

**Update `.env`:**
```bash
nano .env
# Set: AUDIO__MIXER=PCM  (or Master, Speaker)
sudo systemctl restart raspi-ruxpin
```

#### 4. espeak Not Installed

**Error in logs:** `FileNotFoundError: espeak`

**Solution:**
```bash
sudo apt-get update
sudo apt-get install espeak
sudo systemctl restart raspi-ruxpin
```

### Symptom: Audio plays but very quiet

**Check both system volume and app volume:**
```bash
alsamixer
# Increase PCM/Master volume
```

**In web interface:**
- Adjust volume slider
- Check if volume control is working

---

## Servo Issues

### Symptom: Servos don't move

#### 1. Check Wiring

**Verify connections:**
- Eyes PWM → GPIO 21
- Eyes DIR → GPIO 16
- Eyes CDIR → GPIO 20
- Mouth PWM → GPIO 25
- Mouth DIR → GPIO 7
- Mouth CDIR → GPIO 8

**Match with your `.env` file:**
```bash
grep "HARDWARE__.*PWM\|HARDWARE__.*DIR" .env
```

#### 2. Check GPIO Status Panel

**In web interface:**
- Go to System view
- Watch GPIO Status panel
- Click servo controls
- Pins should change color (green=HIGH, red=LOW)

**If pins don't change:**
- GPIO initialization failed
- Check logs for errors

#### 3. Check Power Supply

**Servos need adequate power:**
- Insufficient power → servos won't move
- Use proper power supply (5V, 2-3A minimum)
- Consider separate power for servos

### Symptom: Servos move wrong direction

**Example:** "Close Eyes" opens them instead

**Solution - Swap DIR and CDIR pins:**
```bash
nano .env
```

**For eyes, change:**
```bash
# Before:
HARDWARE__EYES_DIR=16
HARDWARE__EYES_CDIR=20

# After:
HARDWARE__EYES_DIR=20
HARDWARE__EYES_CDIR=16
```

**For mouth, change:**
```bash
# Before:
HARDWARE__MOUTH_DIR=7
HARDWARE__MOUTH_CDIR=8

# After:
HARDWARE__MOUTH_DIR=8
HARDWARE__MOUTH_CDIR=7
```

**Restart and test:**
```bash
sudo systemctl restart raspi-ruxpin
```

### Symptom: Servos move too fast/slow

**Old servos (40+ years) need more time:**

**Adjust duration in `.env`:**
```bash
nano .env
```

**For slower movement:**
```bash
# Eyes (default: 0.8)
HARDWARE__EYES_DURATION=1.2

# Mouth (default: 0.3)
HARDWARE__MOUTH_DURATION=0.5
```

**For faster movement:**
```bash
HARDWARE__EYES_DURATION=0.5
HARDWARE__MOUTH_DURATION=0.2
```

**Restart:**
```bash
sudo systemctl restart raspi-ruxpin
```

### Symptom: Servos don't complete movement

**Possible causes:**
1. Duration too short for old motors
2. Insufficient power
3. Mechanical obstruction

**Solutions:**
1. Increase duration (see above)
2. Check power supply voltage/amperage
3. Check for physical obstructions

### Symptom: Mouth sync looks wrong

**Too fast/jerky:**
```bash
# In backend/services/bear_service.py, line ~195
# Increase sleep duration:
await asyncio.sleep(0.08)  # Was 0.04
```

**Not moving enough:**
```bash
# Check AUDIO__AMPLITUDE_THRESHOLD in .env
AUDIO__AMPLITUDE_THRESHOLD=300  # Lower = more sensitive
```

**Too sensitive:**
```bash
AUDIO__AMPLITUDE_THRESHOLD=700  # Higher = less sensitive
```

---

## WebSocket Connection Issues

### Symptom: "Disconnected" status in web interface

#### 1. Backend Not Running

**Check service:**
```bash
sudo systemctl status raspi-ruxpin
```

**If not running:**
```bash
sudo systemctl start raspi-ruxpin
```

#### 2. Firewall Blocking Port 8080

**Check if port is open:**
```bash
sudo netstat -tulpn | grep 8080
```

**Should show:**
```
tcp  0  0.0.0.0:8080  0.0.0.0:*  LISTEN  1234/python
```

**If blocked by firewall:**
```bash
sudo ufw allow 8080/tcp
```

#### 3. Wrong IP Address

**Get Pi's IP address:**
```bash
hostname -I
```

**Access via:**
```
http://<pi-ip>:8080
```

### Symptom: Connection drops frequently

**Check logs for errors:**
```bash
sudo journalctl -u raspi-ruxpin -f
```

**Possible causes:**
- Network instability
- Backend crashes (check logs)
- Browser tab suspended (refresh)

---

## Performance Issues

### Symptom: Web interface is slow or laggy

#### 1. Raspberry Pi Model

**Check Pi model:**
```bash
cat /proc/cpuinfo | grep Model
```

**Recommendations:**
- Pi 4: Best performance
- Pi 3: Good performance
- Pi Zero: May be slow

#### 2. High CPU Usage

**Check CPU:**
```bash
top
# Press 'q' to quit
```

**If Python process using >80% CPU:**
- Reduce state broadcast rate
- Check for infinite loops in logs

#### 3. Memory Issues

**Check memory:**
```bash
free -h
```

**If low memory:**
- Close other applications
- Consider Pi with more RAM

### Symptom: Audio stutters or cuts out

**Possible causes:**
1. CPU overload
2. Insufficient audio buffer
3. Poor SD card performance

**Solutions:**
1. Reduce background processes
2. Use faster SD card (Class 10 or better)
3. Lower sample rate in `.env`:
```bash
AUDIO__SAMPLE_RATE=8000  # Lower quality, less CPU
```

---

## Development Issues

### Symptom: Changes don't appear

#### 1. Frontend Changes

**Need to rebuild:**
```bash
cd frontend
npm run build
cd ..
sudo systemctl restart raspi-ruxpin
```

**Or use development mode:**
```bash
# Terminal 1 - Backend
uv run python -m backend.main

# Terminal 2 - Frontend
cd frontend
npm run dev
# Access: http://localhost:5173
```

#### 2. Backend Changes

**Restart service:**
```bash
sudo systemctl restart raspi-ruxpin
```

**Or run manually for development:**
```bash
uv run python -m backend.main
# Includes --reload for auto-restart on changes
```

### Symptom: Mock GPIO on Pi

**If you see "Using mock GPIO" in logs:**

**Check `.env`:**
```bash
grep MOCK_GPIO .env
```

**Should be:**
```bash
HARDWARE__USE_MOCK_GPIO=false
```

**If wrong:**
```bash
nano .env
# Fix the value
sudo systemctl restart raspi-ruxpin
```

---

## Getting Help

### Collect Debug Information

**1. Service status:**
```bash
sudo systemctl status raspi-ruxpin
```

**2. Recent logs:**
```bash
sudo journalctl -u raspi-ruxpin -n 200 --no-pager
```

**3. Configuration:**
```bash
cat .env
```

**4. System info:**
```bash
cat /proc/cpuinfo | grep Model
cat /proc/cpuinfo | grep Hardware
python --version
node --version
```

**5. Audio devices:**
```bash
aplay -l
amixer scontrols
```

**6. GPIO groups:**
```bash
groups
```

### Enable Debug Logging

**Edit `.env`:**
```bash
nano .env
```

**Set:**
```bash
DEBUG=true
```

**Restart:**
```bash
sudo systemctl restart raspi-ruxpin
```

**Watch debug logs:**
```bash
sudo journalctl -u raspi-ruxpin -f
```

### Common Log Messages

**Normal:**
```
Using RPi.GPIO for production
GPIO initialized with BCM mode
BearService started successfully
Application startup complete
```

**Warning (usually OK):**
```
User added to gpio group
Eye blinking disabled
```

**Error (needs fixing):**
```
Failed to initialize GPIO
ModuleNotFoundError
Permission denied
Connection refused
```

---

## Quick Reference

### Essential Commands

```bash
# Service management
sudo systemctl status raspi-ruxpin
sudo systemctl restart raspi-ruxpin
sudo journalctl -u raspi-ruxpin -f

# Audio testing
speaker-test -t wav -c 2
aplay -l
alsamixer

# Configuration
nano .env
cat .env | grep HARDWARE

# Network
hostname -I
sudo netstat -tulpn | grep 8080

# Groups
groups
sudo usermod -a -G gpio,audio pi
```

### Files to Check

- `/etc/systemd/system/raspi-ruxpin.service` - Service definition
- `/home/pi/raspi-ruxpin/.env` - Configuration
- `/home/pi/raspi-ruxpin/frontend/dist/` - Built frontend
- `/home/pi/raspi-ruxpin/.venv/` - Python virtual environment

### Useful Links

- [Main README](README.md)
- [Quick Start Guide](QUICKSTART.md)
- [GitHub Repository](https://github.com/yourusername/raspi-ruxpin)

---

## Still Having Issues?

If this guide didn't solve your problem:

1. Check the logs carefully for specific error messages
2. Search the error message online
3. Create an issue on GitHub with:
   - Description of the problem
   - Steps to reproduce
   - Log output
   - System information

Remember: Most issues are configuration-related. Double-check your `.env` file and GPIO pin numbers!
