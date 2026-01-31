# Raspi Ruxpin 2.0

![creepy bear](https://raw.githubusercontent.com/yamanote1138/raspi-ruxpin/master/public/img/teddy_eomo.png)

Modern animatronic bear control system with FastAPI and Vue 3!

**Version 2.0** - Complete modernization with:
- 🚀 FastAPI backend with WebSocket support
- 🎨 Vue 3 + TypeScript + Vite frontend
- 🔧 Async hardware control
- 📦 Modern dependency management
- 🧪 Full type safety
- 💻 Mac development support (no hardware required!)

Make a creepy old Teddy Ruxpin say whatever you want with synchronized mouth movements!

## Introduction

This project was originally based on the [version](https://www.hackster.io/chip/c-h-i-p-py-ruxpin-5f02f1) constructed by the nice folks at NextThing, inc. Version 2.0 is a complete modernization with best practices for Python and Vue development.

## Features

- 🎭 **Puppet Mode**: Manually control eyes and mouth
- 🗣️ **Speak Mode**: Text-to-speech with mouth synchronization
- 🎵 **Phrase Library**: Pre-recorded audio clips from movies/TV
- 🔊 **Volume Control**: Adjust system volume on the fly
- 🌐 **Web Interface**: Modern responsive UI with Bootstrap 5
- 🔄 **Real-time Updates**: WebSocket communication for instant feedback
- 🧪 **Mock Hardware**: Develop on Mac without Raspberry Pi

## Quick Start

### Mac Development (No Hardware Required)

**Prerequisites:**
- Install [uv](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`
- Install [Node.js](https://nodejs.org/)

```bash
# 1. Create virtual environment
uv venv

# 2. Install Python dependencies
uv pip install -e ".[dev,mock]"

# 3. Install frontend dependencies
cd frontend
npm install
cd ..

# 4. Create .env file
cp .env.example .env

# 5. Start backend (Terminal 1)
uv run python -m backend.main

# 6. Start frontend dev server (Terminal 2)
cd frontend
npm run dev

# 7. Open browser
# http://localhost:5173
```

### Raspberry Pi Production

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

## Project Structure

```
raspi-ruxpin/
├── backend/                 # Python backend
│   ├── main.py             # FastAPI app entry point
│   ├── config.py           # Pydantic settings
│   ├── dependencies.py     # FastAPI DI
│   ├── api/                # API endpoints
│   │   ├── websocket.py    # WebSocket handler
│   │   └── endpoints/      # REST endpoints
│   ├── services/           # Business logic
│   │   └── bear_service.py # Bear orchestration
│   ├── hardware/           # Hardware abstraction
│   │   ├── gpio_manager.py # GPIO lifecycle
│   │   ├── servo.py        # Async servo control
│   │   └── audio_player.py # Async audio
│   └── core/               # Domain models
├── frontend/               # Vue 3 + TypeScript
│   ├── src/
│   │   ├── components/     # Vue SFCs
│   │   ├── composables/    # useBear, useWebSocket
│   │   └── types/          # TypeScript types
│   ├── vite.config.ts
│   └── package.json
├── config/                 # Configuration
│   └── phrases.json        # Audio phrase library
├── sounds/                 # Audio files
├── pyproject.toml          # Python packaging
└── .env                    # Environment config
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8080

# Hardware (Mac: set USE_MOCK_GPIO=true)
HARDWARE__USE_MOCK_GPIO=false
HARDWARE__EYES_PWM=21
HARDWARE__MOUTH_PWM=25

# Audio
AUDIO__START_VOLUME=100
TTS__ENGINE=espeak
TTS__VOICE=en+m3
```

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

### Backend Development

```bash
# Run with auto-reload
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080

# Type checking
uv run mypy backend/

# Linting
uv run ruff check backend/
uv run black backend/

# Testing
uv run pytest --cov=backend
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

## API Documentation

Once running, visit:
- API docs: http://localhost:8080/docs
- Health check: http://localhost:8080/api/health
- System status: http://localhost:8080/api/status

## WebSocket Protocol

Connect to `/ws` and send JSON messages:

```javascript
// Update bear positions
{ "type": "update_bear", "eyes": "open", "mouth": "closed" }

// Speak text
{ "type": "speak", "text": "Hello world" }

// Play phrase
{ "type": "play", "sound": "starwars_iamyourfather" }

// Set volume
{ "type": "set_volume", "level": 75 }
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

- **2.0.0** - Complete modernization with FastAPI + Vue 3
- **1.0.0** - Original Vue 2 + aiohttp version
