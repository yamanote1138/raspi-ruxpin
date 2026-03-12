# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspi Ruxpin 2.0 — an animatronic Teddy Ruxpin control system with a FastAPI/WebSocket backend and Vue 3 frontend. The bear has two servos (eyes and mouth) controlled via GPIO, with TTS and audio playback synchronized to mouth movements.

## Commands

```bash
# Install all dependencies (Mac dev)
make install

# Run backend server
make run                    # production mode
make dev                    # development mode with auto-reload

# Run frontend dev server (separate terminal)
make frontend               # http://localhost:5173

# Tests
make test                   # run all tests
make test-verbose           # verbose output
make test-cov               # with coverage
uv run pytest backend/tests/test_servo.py           # single test file
uv run pytest backend/tests/test_servo.py::TestServo::test_open  # single test

# Code quality
make lint                   # ruff check backend/
make format                 # ruff format backend/
make type-check             # mypy backend/ (strict mode)
make check                  # all three: lint + type-check + test
```

## Architecture

### Backend (Python 3.12, FastAPI)

**Entry point:** `backend/main.py` — FastAPI app with lifespan manager that wires up all services.

**Startup flow:** `lifespan()` creates `GPIOManager` → `AudioPlayer` → `BearService`, stores them on `app.state`. Services are accessed via `backend/dependencies.py` (FastAPI DI) or directly from `app.state` in the WebSocket handler.

**Key layers:**
- `backend/config.py` — Pydantic Settings with nested config classes (`HardwareSettings`, `AudioSettings`, `TTSSettings`). Config precedence: env vars > YAML (`config/hardware.yaml`) > defaults. Singleton via `get_settings()`.
- `backend/services/bear_service.py` — Central orchestrator. Owns two `Servo` instances (eyes, mouth) and an `AudioPlayer`. Runs two background asyncio tasks: `_talk_monitor` (25Hz mouth sync from audio amplitude) and `_blink_monitor` (random eye blinks).
- `backend/hardware/servo.py` — Async servo control with PWM. Uses `asyncio.Lock` per servo, animates position with linear interpolation. Supports both binary open/close and proportional `set_position_percent()`.
- `backend/hardware/gpio_manager.py` — Wraps RPi.GPIO or mock_gpio behind a Protocol. Tracks active pins/PWMs for clean shutdown.
- `backend/hardware/audio_player.py` — Platform-aware audio (afplay on Mac, aplay on Linux). Reads WAV amplitude data and updates `_current_amplitude` at 50Hz for mouth sync. TTS via espeak (Linux), macOS `say`, or Piper neural TTS.
- `backend/api/websocket.py` — All client communication is WebSocket-based (no REST for control). Message types are Pydantic models with `Literal` type discriminators. A `ConnectionManager` handles multi-client broadcast. State broadcasts at 10Hz, GPIO status at 1Hz.

**Hardware abstraction:** On Mac, `backend/hardware/mock_gpio.py` provides a mock GPIO module. Controlled by `HARDWARE__USE_MOCK_GPIO` env var (auto-detected from platform).

### Frontend (Vue 3 + TypeScript + Vite)

- `frontend/src/composables/useWebSocket.ts` — WebSocket singleton managing connection to `/ws`
- `frontend/src/composables/useBear.ts` — Bear state management composable
- Components: `ControlMode.vue` (primary interface), `ConfigMode.vue` (logs/settings), `BearVisualization.vue` (interactive bear display)

### Communication

All real-time control uses WebSocket at `/ws`. Message types: `update_bear`, `speak`, `play`, `set_volume`, `set_blink_enabled`, `set_character`, `set_log_level`, `fetch_phrases`, `get_gpio_status`. Server pushes `bear_state`, `log`, `gpio_status`, `error`, `success`.

## Key Constraints

- **Volume capped at 90%** — values above 90 cause system instability on the Pi hardware
- **Servo durations max 2.0s** — old 40+ year old servos need tuned timing
- **Mouth sync at 25Hz** in `_talk_monitor`, audio amplitude updates at 50Hz
- **Python 3.12 required** — uses `X | Y` union syntax throughout
- **mypy strict mode** enabled — all code must be fully typed
- **ruff** for linting/formatting, line length 100
- **pytest with asyncio_mode=auto** — async test functions just work
- **Test markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.hardware`

## Environment

Copy `.env.example` to `.env`. Key variables use double-underscore nesting: `HARDWARE__USE_MOCK_GPIO`, `AUDIO__START_VOLUME`, `TTS__ENGINE`, etc.
