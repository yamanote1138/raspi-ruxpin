# Raspi Ruxpin 2.0 - Quick Start Guide

## Installation

### Prerequisites

**Install uv (Python package manager):**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or with Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Install Node.js:**
- Download from https://nodejs.org/

### Automated Setup (Recommended)

```bash
# Run setup script
./scripts/setup-dev.sh
```

This will:
- Check for uv installation
- Create virtual environment with uv
- Create `.env` file with appropriate settings
- Install Python dependencies (with mock GPIO for Mac)
- Install frontend dependencies
- Create necessary directories

### Manual Setup

**On macOS:**
```bash
# 1. Create virtual environment
uv venv

# 2. Create .env file from Mac template
cp .env.example.mac .env

# 3. Install Python dependencies
uv pip install -e ".[dev]"

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Create TTS directory
mkdir -p sounds/tts
```

**On Raspberry Pi:**
```bash
# 1. Create virtual environment
uv venv

# 2. Create .env file from Pi template
cp .env.example.pi .env

# 3. Install Python dependencies with hardware support
uv pip install -e ".[hardware]"

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Create TTS directory
mkdir -p sounds/tts
```

## Running the Application

### Development Mode (Mac/Linux)

**Terminal 1 - Backend:**
```bash
uv run python -m backend.main
# or: source .venv/bin/activate && python -m backend.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Browser:**
```
http://localhost:5173
```

The frontend dev server will proxy API and WebSocket requests to the backend.

### Production Mode (Raspberry Pi)

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Run backend (serves built frontend)
uv run python -m backend.main
```

**Browser:**
```
http://<raspberry-pi-ip>:8080
```

## First Run Checklist

1. ✅ Backend starts without errors
2. ✅ Frontend dev server starts
3. ✅ Browser shows Raspi Ruxpin UI
4. ✅ Connection status shows "Connected" (green)
5. ✅ Can switch between Puppet and Speak modes
6. ✅ Bear image updates when clicking controls
7. ✅ Volume slider works
8. ✅ Phrases load in dropdown

## Testing the Interface

### Puppet Mode

1. Click "Puppet Mode" button
2. Click "Open Eyes" - bear image should update
3. Click "Close Eyes" - bear image should update
4. Click "Open Mouth" - bear image should update
5. Click "Close Mouth" - bear image should update
6. Try clicking directly on bear's eyes/mouth

### Speak Mode

1. Click "Speak Mode" button
2. Adjust volume slider - should see volume change
3. Type text in the text area
4. Click "Speak" - on Mac, should hear TTS through speakers
5. Select a phrase from dropdown
6. Click "Play Phrase" - should hear audio

## On Mac (Mock Hardware)

When running on Mac with mock GPIO:

**What Works:**
- ✅ Full web interface
- ✅ Bear state updates
- ✅ WebSocket communication
- ✅ TTS generation and playback
- ✅ Audio file playback
- ✅ Volume control (Mac system volume)
- ✅ Console logging of GPIO operations

**What Doesn't Work:**
- ❌ Actual servo movement (no hardware)
- ❌ Hardware GPIO pins (mocked)

Check the terminal for mock GPIO logs to see what would be sent to hardware.

## On Raspberry Pi (Real Hardware)

When running on Pi with real GPIO:

**Additional Setup Required:**
1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install espeak alsa-utils python3-dev
   ```

3. Create Pi-specific `.env` file:
   ```bash
   cp .env.example.pi .env
   # Verify pin numbers match your wiring!
   ```

4. Wire up servos according to hardware guide

5. Run with sudo if needed for GPIO access:
   ```bash
   sudo uv run python -m backend.main
   ```

## Common Issues

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
- **Solution:** Run `uv pip install -e ".[dev]"`

**Error:** `command not found: uv`
- **Solution:** Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Error:** `GPIO not found`
- **Solution:** On Pi, install RPi.GPIO: `uv pip install RPi.GPIO`
- **Note:** Mac development uses built-in mock GPIO (no installation needed)

### Frontend won't start

**Error:** `command not found: npm`
- **Solution:** Install Node.js from https://nodejs.org/

**Error:** `Cannot find module 'vue'`
- **Solution:** `cd frontend && npm install`

### WebSocket won't connect

**Error:** Connection status shows "Disconnected"
- **Solution:** Make sure backend is running on port 8080
- **Solution:** Check browser console for errors
- **Solution:** Try refreshing the page

### No sound on Mac

**Issue:** Can't hear TTS or audio
- **Solution:** Check Mac system volume
- **Solution:** Check that audio files exist in `sounds/` directory
- **Solution:** Verify espeak is installed: `brew install espeak`

## API Endpoints

Once running, explore:

- **Health Check:** http://localhost:8080/api/health
- **System Status:** http://localhost:8080/api/status
- **API Docs:** http://localhost:8080/docs
- **WebSocket:** ws://localhost:8080/ws

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:
- Backend: Uses `uvicorn --reload`
- Frontend: Vite HMR

Just save your files and see changes instantly!

### Type Checking

```bash
# Backend
uv run mypy backend/

# Frontend
cd frontend && npm run type-check
```

### Linting

```bash
# Backend
uv run ruff check backend/
uv run black backend/

# Frontend
cd frontend && npm run lint
```

### Debugging

Add breakpoints in VS Code or use print statements. Console logs appear in:
- Backend logs: Terminal running `python -m backend.main`
- Frontend logs: Browser Developer Console
- GPIO logs: Backend terminal (when using mock GPIO on Mac)

## Next Steps

1. **Customize Configuration**
   - Edit `.env` for your setup (use `.env.example.mac` or `.env.example.pi` as starting point)
   - Add custom phrases to `config/phrases.json`
   - Add custom sounds to `sounds/` directory

2. **Deploy to Pi**
   - Follow hardware setup guide
   - Build and deploy
   - Test with real hardware

3. **Contribute**
   - Add new features
   - Write tests (Phase 8)
   - Improve documentation

## Getting Help

- Check `IMPLEMENTATION_SUMMARY.md` for technical details
- Review `README.md` for full documentation
- See the [wiki](https://github.com/yamanote1138/raspi-ruxpin/wiki/) for hardware guides

## Success!

If you see the bear interface and can control it, you're all set! The modernization is complete and working. 🎉

Enjoy your modernized Raspi Ruxpin!
