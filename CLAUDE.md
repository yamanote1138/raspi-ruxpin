# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspi Ruxpin 2.0 — an animatronic Teddy Ruxpin control system. A Raspberry Pi (or Mac in dev) serves as the brain: audio playback, analysis, web UI. An Arduino handles all motor control via serial. The Pi's audio output is Y-split — one end to speaker, one end to Arduino's analog input for realtime mode.

Two servos: eyes (open/close/blink) and mouth (7-position model: C/T/S/N/M/L/W). Both 5-wire H-bridge (original Teddy Ruxpin) and 3-wire standard servos are supported via Arduino firmware abstraction.

## Commands

```bash
# Install all dependencies (Mac dev)
make install

# Run backend server
make run                    # production mode
make dev                    # development mode with auto-reload (port 8888)

# Run frontend dev server (separate terminal)
make frontend               # http://localhost:5173

# Tests
make test                   # run all tests
make test-verbose           # verbose output
make test-cov               # with coverage
uv run pytest backend/tests/test_arduino.py        # single test file

# Code quality
make lint                   # ruff check backend/
make format                 # ruff format backend/
make type-check             # mypy backend/ (strict mode)
make check                  # all three: lint + type-check + test

# CLI (standalone, no web UI)
uv run raspi-ruxpin-cli
```

## Architecture

### Three Sync Modes

- **Amplitude**: Pi pre-analyzes WAV amplitude in 20ms windows, caches timing CSV, sends timed `M<code>` commands over serial during playback.
- **Phoneme**: Pi uses Whisper + phonemizer to analyze phonemes, caches timing CSV, sends timed commands. Requires `uv pip install -e '.[phoneme]'` and `espeak-ng`.
- **Realtime**: Arduino reads audio signal from ADC pin A0, computes RMS, drives servos autonomously. Reports `MOUTH:<code>` over serial for frontend visualization.

### Backend (Python 3.12, FastAPI)

**Entry point:** `backend/main.py` — FastAPI app with lifespan manager.

**Startup flow:** `lifespan()` creates `ArduinoController` → `AudioPlayer` → `TimingStore` → `BearService` → `bear_service.start()`. Services stored on `app.state`.

**Key layers:**
- `backend/config.py` — Pydantic Settings with nested classes (`AudioSettings`, `TTSSettings`, `SerialSettings`, `SyncSettings`). Config precedence: env vars > YAML > defaults. Singleton via `get_settings()`.
- `backend/services/bear_service.py` — Central orchestrator. Owns `ArduinoController`, `AudioPlayer`, `TimingStore`. Runs background tasks: `_talk_monitor` (cleanup after playback) and `_blink_monitor` (random eye blinks). `_perform_playback()` handles the common speak/play flow. `_execute_timing_schedule()` dispatches timed serial commands synced to audio via `asyncio.Event`.
- `backend/hardware/arduino.py` — Async serial controller. Handles handshake, config, runtime commands. Background reader intercepts `MOUTH:<code>` reports (realtime mode) via callback. All serial I/O via `asyncio.to_thread`.
- `backend/hardware/mock_serial.py` — Mock for Mac dev. Simulates READY/OK/PONG. In realtime mode, generates simulated mouth position reports during audio playback (triggered by `AUDIO:START`/`AUDIO:STOP`).
- `backend/hardware/audio_player.py` — Platform-aware audio (afplay on Mac, aplay on Linux). Supports `start_callback` for timing sync. TTS via espeak or Piper.
- `backend/hardware/audio_analyzer.py` — Amplitude and phoneme analysis. Produces `list[tuple[int, MouthPosition]]` timelines.
- `backend/cli/audio_quality.py` — WAV quality scoring for mouth animation suitability. Scores 0–100 across position variety, activity balance, signal strength, and noise floor. Used by CLI menu's quality analysis view.
- `backend/hardware/timing_store.py` — Caches analysis results as CSV in `data/timing/`.
- `backend/hardware/calibration.py` — 7-position jaw calibration table with interpolation.
- `backend/api/websocket.py` — All client communication is WebSocket-based at `/ws`. Message routing via `_MESSAGE_HANDLERS` dict. State broadcasts at 10Hz, logs streamed in realtime.

### Arduino Firmware (`arduino/ruxpin/ruxpin.ino`)

State machine: BOOT → HANDSHAKE → CONFIG → RUNNING. Serial protocol: 115200 baud, newline-terminated ASCII.

**Commands:** `M<code>` (mouth position), `J<u>,<l>` (direct angles), `EO`/`EC`/`EB` (eyes), `MODE:<mode>`, `PING`, `STATUS`, `AUDIO:START`/`AUDIO:STOP` (informational).

**Servo abstraction:** H-bridge (PWM + DIR + CDIR, timed movements) or Standard (Servo.h, direct angles).

**ADC processing (realtime mode):** Reads A0 at ~50Hz, 20ms RMS windows, 0.7 power compression, 7-threshold mapping. Reports position changes via `MOUTH:<code>\n`.

### Frontend (Vue 3 + TypeScript + Vite)

**Layout:** 2-column on wide screens (≥992px), single-column stacked on narrow. Left column: bear image. Right column: controls, phrase player, TTS — stacked vertically.

- `frontend/src/composables/useWebSocket.ts` — WebSocket singleton at `/ws`
- `frontend/src/composables/useBear.ts` — Bear state management, mode switching, change-detection logging
- `frontend/src/components/BearVisualization.vue` — Bear image display (purely visual, no interaction)
- `frontend/src/components/BearControls.vue` — Eyes/mouth/blink toggles, volume, sync mode cycling, socket/arduino status, info modal trigger
- `frontend/src/components/PhrasePlayer.vue` — Phrase selection dropdown with random and play buttons
- `frontend/src/components/TTSControls.vue` — Text-to-speech textarea with random, clear, and speak buttons

### Communication

All real-time control uses WebSocket at `/ws`. Message types: `update_bear`, `speak`, `play`, `set_volume`, `set_blink_enabled`, `set_sync_mode`, `fetch_phrases`. Server pushes `bear_state` (10Hz), `error`, `success`, `phrases`. Character selection (`set_character`) is config-only (not exposed in UI).

## Key Constraints

- **Volume capped at 90%** — values above 90 cause system instability on the Pi
- **Python 3.12 required** — uses `StrEnum`, `X | Y` union syntax
- **mypy strict mode** enabled — all code must be fully typed
- **ruff** for linting and formatting, line length 100
- **pytest with asyncio_mode=auto** — async test functions just work
- **Test markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.hardware`

## Data Directories

- `data/sounds/` — WAV audio clips
- `data/timing/` — Cached analysis CSVs (`{stem}_{amp|phn}.csv`)
- `data/tts/` — Generated TTS audio files (gitignored)
- `config/` — `jaw_calibration.json`

## Environment

Copy `.env` and adjust. Key variables use double-underscore nesting: `SERIAL__USE_MOCK`, `AUDIO__START_VOLUME`, `SYNC__MODE`, `TTS__ENGINE`, etc. Serial mock is auto-detected on macOS.
