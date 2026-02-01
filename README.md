# Raspi Ruxpin 2.0

![creepy bear](https://raw.githubusercontent.com/yamanote1138/raspi-ruxpin/master/public/img/teddy_eomo.png)

Modern animatronic bear control system with FastAPI and Vue 3!

**Version 2.0** - Complete modernization with:
- 🚀 FastAPI backend with WebSocket support
- 🎨 Vue 3 + TypeScript + Vite frontend
- 🔧 Async hardware control
- 📦 Modern dependency management with [uv](https://github.com/astral-sh/uv) (10-100x faster than pip!)
- 🧪 Full type safety
- 💻 Mac development support (no hardware required!)

Make a creepy old Teddy Ruxpin say whatever you want with synchronized mouth movements!

## Introduction

This project was originally based on the [version](https://www.hackster.io/chip/c-h-i-p-py-ruxpin-5f02f1) constructed by the nice folks at NextThing, inc. Version 2.0 is a complete modernization with best practices for Python and Vue development.

## Features

- 🎮 **Control Mode**: Unified interface for bear control
  - Interactive bear status panel with clickable controls
  - Text-to-speech with synchronized mouth movements
  - Phrase library with pre-recorded audio
  - Real-time volume control
  - Auto-blink toggle
- 📊 **Config Mode**: System monitoring and configuration
  - Real-time log viewer with level filtering
  - Bear status monitoring
  - System settings management
- 🌐 **Modern Web Interface**: Responsive design with Bootstrap 5
  - Clean, playful UI with rounded fonts
  - Mobile-friendly layout
  - Real-time status updates
- 🔄 **WebSocket Communication**: Instant bi-directional updates
- 🎙️ **Multiple TTS Engines**: Support for espeak, macOS built-in, and Piper
- 🧪 **Mock Hardware**: Full development on Mac without Raspberry Pi

## Quick Start

### Mac Development (No Hardware Required)

**Prerequisites:**
- Install [uv](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`
- Install [Node.js](https://nodejs.org/)

**Quick Setup with Makefile:**
```bash
# Install all dependencies
make install

# Create .env file
cp .env.example .env

# Start backend (Terminal 1)
make run

# Start frontend dev server (Terminal 2)
make frontend

# Open browser at http://localhost:5173
```

**Manual Setup:**
```bash
# 1. Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev,mock]"

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. Create .env file
cp .env.example .env

# 4. Start backend (Terminal 1)
uv run python -m backend.main

# 5. Start frontend dev server (Terminal 2)
cd frontend && npm run dev

# 6. Open browser at http://localhost:5173
```

### Raspberry Pi Production

**Quick Deploy:**
```bash
# Clone the repository
git clone https://github.com/yourusername/raspi-ruxpin.git
cd raspi-ruxpin

# Run deployment script (installs everything and sets up systemd service)
./scripts/deploy.sh
```

**Manual Setup:**
```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create virtual environment and install Python dependencies
uv venv
uv pip install -e ".[hardware]"

# 3. Install system dependencies
sudo apt-get install espeak alsa-utils

# 4. Build frontend
cd frontend
npm install
npm run build
cd ..

# 5. Configure environment
cp .env.example .env
# Edit .env and set HARDWARE__USE_MOCK_GPIO=false

# 6. Run backend (serves built frontend)
uv run python -m backend.main
```

For detailed production deployment instructions including systemd service setup, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Project Structure

```
raspi-ruxpin/
├── backend/                    # Python backend
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # Pydantic settings with env vars
│   ├── dependencies.py        # FastAPI dependency injection
│   ├── logging_config.py      # Logging with WebSocket streaming
│   ├── api/                   # API layer
│   │   ├── websocket.py       # WebSocket endpoint
│   │   └── endpoints/         # REST endpoints
│   ├── services/              # Business logic
│   │   └── bear_service.py    # Bear orchestration & control
│   ├── hardware/              # Hardware abstraction
│   │   ├── gpio_manager.py    # GPIO lifecycle management
│   │   ├── servo.py           # Async servo control
│   │   ├── audio_player.py    # Async audio playback
│   │   └── models.py          # Hardware Pydantic models
│   └── core/                  # Domain models
│       ├── enums.py           # State, Direction enums
│       └── exceptions.py      # Custom exceptions
├── frontend/                  # Vue 3 + TypeScript + Vite
│   ├── src/
│   │   ├── main.ts           # App entry point
│   │   ├── App.vue           # Root component
│   │   ├── components/       # Vue SFCs
│   │   │   ├── BearVisualization.vue
│   │   │   ├── ControlMode.vue
│   │   │   ├── ConfigMode.vue
│   │   │   ├── LogViewer.vue
│   │   │   └── StatusBar.vue
│   │   ├── composables/      # Vue composables
│   │   │   ├── useBear.ts    # Bear state management
│   │   │   └── useWebSocket.ts # WebSocket singleton
│   │   └── types/            # TypeScript definitions
│   ├── vite.config.ts        # Vite configuration
│   ├── tsconfig.json         # TypeScript config
│   └── package.json          # Node dependencies
├── config/                    # Configuration files
│   └── phrases.json          # Audio phrase library
├── sounds/                    # Audio files (WAV)
├── public/                    # Static assets
│   └── img/                  # Bear images
├── pyproject.toml            # Python packaging & dependencies
├── .env.example              # Environment template
└── .env                      # Environment config (create from example)
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
ENVIRONMENT=development
DEBUG=true              # Enable debug mode (sets log level to DEBUG)
HOST=0.0.0.0
PORT=8080

# Hardware (Mac: set USE_MOCK_GPIO=true for development)
HARDWARE__USE_MOCK_GPIO=false
HARDWARE__EYES_PWM=21
HARDWARE__EYES_DIR=16
HARDWARE__EYES_CDIR=20
HARDWARE__MOUTH_PWM=25
HARDWARE__MOUTH_DIR=7
HARDWARE__MOUTH_CDIR=8

# Audio
AUDIO__START_VOLUME=100
AUDIO__MIXER=PCM        # ALSA mixer name (Linux only)

# Text-to-Speech
TTS__ENGINE=espeak      # Options: espeak, piper, macos
TTS__VOICE=en+m3        # Voice (espeak: en+m3, piper: model path)
TTS__SPEED=125          # Speech speed
TTS__PITCH=50           # Voice pitch
```

**TTS Engine Options:**
- `espeak` - Available on Linux (apt install espeak)
- `piper` - High-quality neural TTS (install with `uv pip install piper-tts`)
- `macos` - Uses macOS built-in TTS (Mac development only)

### Hardware Configuration (Optional)

Create `config/hardware.yaml` to override settings:

```yaml
hardware:
  eyes_speed: 100
  eyes_duration: 0.4
  mouth_speed: 100
  mouth_duration: 0.15
```

## Development

### Common Commands (using Makefile)

```bash
# Show all available commands
make help

# Run backend with auto-reload
make dev

# Run frontend dev server
make frontend

# Run tests
make test              # Basic test run
make test-verbose      # With verbose output
make test-cov          # With coverage report

# Code quality
make lint              # Run linters
make format            # Format code
make type-check        # Run type checker
make check             # Run all checks (lint, type-check, test)

# Cleanup
make clean             # Remove build artifacts and caches
```

### Backend Development (using uv directly)

```bash
# Run with auto-reload
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080

# Type checking
uv run mypy backend/

# Linting and formatting
uv run ruff check backend/
uv run ruff format backend/

# Testing
uv run pytest --cov=backend --cov-report=html
```

### Frontend Development

```bash
cd frontend

# Dev server with hot reload
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build
```

## Using the Interface

The web interface has two main views:

### Control Mode
The primary control interface with three sections:
- **Bear Status Panel** (top): Interactive bear image and status controls
  - Click bear image to toggle eyes/mouth (or use buttons)
  - Button bar: Eyes, Mouth, Blink, and Status indicators
  - Volume dropdown (0-100% in 20% increments)
- **Phrase Library** (left): Play pre-recorded audio clips
  - Select from dropdown and click "Play Phrase"
- **Text-to-Speech** (right): Generate speech from text
  - Type text and click "Speak"
  - Mouth movements sync with audio amplitude

### Config Mode
System monitoring and settings:
- **System Logs**: Real-time log viewer
  - Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Auto-scroll toggle
  - Clear logs button
  - Shows WebSocket events, GPIO operations, audio playback, etc.

## API Documentation

Once running, visit:
- **Web UI**: http://localhost:8080 (or http://localhost:5173 in dev mode)
- **API docs**: http://localhost:8080/docs
- **Health check**: http://localhost:8080/api/health

## WebSocket Protocol

Connect to `/ws` and send JSON messages:

```javascript
// Update bear positions
{ "type": "update_bear", "eyes": "open", "mouth": "closed" }

// Speak text with TTS
{ "type": "speak", "text": "Hello world" }

// Play pre-recorded phrase
{ "type": "play", "sound": "starwars_iamyourfather" }

// Set volume (0-100)
{ "type": "set_volume", "level": 75 }

// Toggle auto-blink
{ "type": "set_blink_enabled", "enabled": true }

// Change log level
{ "type": "set_log_level", "level": "DEBUG" }

// Fetch available phrases
{ "type": "fetch_phrases" }
```

**Received Messages:**

```javascript
// Bear state updates
{ "type": "bear_state", "data": { "eyes": "open", "mouth": "closed", "volume": 75, ... } }

// Available phrases
{ "type": "phrases", "data": { "phrase_key": "Description", ... } }

// Log messages (streamed in real-time)
{ "type": "log", "data": { "level": "INFO", "message": "...", "timestamp": 1234567890, ... } }

// Error messages
{ "type": "error", "message": "Error description" }

// Success confirmations
{ "type": "success", "message": "Operation completed" }
```

## Hardware Setup

See the [wiki](https://github.com/yamanote1138/raspi-ruxpin/wiki/) for detailed hardware setup instructions.

## Documentation

Detailed instructions available in the [wiki](https://github.com/yamanote1138/raspi-ruxpin/wiki/):
- [Hardware Setup](https://github.com/yamanote1138/raspi-ruxpin/wiki/Hardware-Setup)
- [Software Installation](https://github.com/yamanote1138/raspi-ruxpin/wiki/Software-Installation)
- [Operation](https://github.com/yamanote1138/raspi-ruxpin/wiki/Operation)
- [Troubleshooting](https://github.com/yamanote1138/raspi-ruxpin/wiki/Troubleshooting)

## License

MIT

## Version History

- **2.0.0** (2025) - Complete modernization
  - FastAPI backend with async/await patterns
  - Vue 3 + TypeScript + Vite frontend
  - Unified Control mode interface
  - Real-time log viewer with WebSocket streaming
  - Multiple TTS engine support (espeak, piper, macOS)
  - Modern responsive UI with Bootstrap 5
  - Comprehensive deployment automation
  - Full type safety throughout
  - Mac development support with Mock GPIO
- **1.0.0** (2023) - Original Vue 2 + aiohttp version
