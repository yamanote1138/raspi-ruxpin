# Raspi Ruxpin 2.0

![creepy bear](https://raw.githubusercontent.com/yamanote1138/raspi-ruxpin/master/public/img/teddy_eomo.png)

Make a creepy old Teddy Ruxpin say whatever you want, with his mouth moving in time.

A Raspberry Pi (or your Mac, while you're developing) plays the audio and figures out how the mouth should move. An Arduino runs the motors. You drive it all from a web page or a terminal menu.

## How it works

```
                      ┌──────────────────────────────┐
  Browser / CLI ─────►│  Pi or Mac (the brain)       │
   (WebSocket)        │  • plays audio               │
                      │  • analyzes it for mouth     │
                      │    movement                  │
                      │  • serves the web UI         │
                      └──────┬───────────────┬───────┘
                             │ USB serial    │ audio out
                             ▼               ▼
                      ┌────────────┐    ┌─────────┐
                      │  Arduino   │◄───┤ Y-split ├──► speaker
                      │  (motors)  │ A0 └─────────┘
                      └─────┬──────┘
                            ▼
                    eyes + mouth servos
```

The bear has two moving parts: **eyes** (open, closed, blink) and a **mouth** with seven positions. Both the original 5-wire H-bridge motors and regular 3-wire hobby servos work.

### Three ways to sync the mouth

| Mode | Who does the work | Good for |
|------|-------------------|----------|
| **Amplitude** | The Pi checks how loud each 20ms slice of the clip is ahead of time, then sends timed mouth commands | The default. Works everywhere |
| **Phoneme** | The Pi transcribes the clip (Whisper) and works out the mouth shapes from the sounds | Better-looking speech, but needs extra packages |
| **Realtime** | The Arduino listens to the audio signal on pin A0 and moves the mouth on its own | Lowest latency, no analysis step |

Amplitude and phoneme results are cached in `data/timing/`, so a clip is only analyzed once.

## Features

- Web interface: bear picture, eye/mouth/blink controls, volume, sync mode, clip player, and text-to-speech
- Terminal menu (`raspi-ruxpin-cli`) for playing clips, speaking text, testing the servos, and scoring audio files
- Text-to-speech with espeak, macOS `say`, or Piper
- Audio quality scoring so you can tell if a clip will animate well
- Full Mac development with a fake Arduino, so you don't need hardware to work on the software

## Quick start (Mac, no hardware)

You need [uv](https://github.com/astral-sh/uv) (`brew install uv`) and [Node.js](https://nodejs.org/) 20 or newer.

```bash
make install                 # Python + frontend dependencies
cp .env.example.mac .env

make dev                     # backend on http://localhost:8888
make frontend                # in a second terminal: UI on http://localhost:5173
```

Open http://localhost:5173 and play a clip. The mock Arduino is turned on automatically on a Mac.

More detail is in the [Quick Start guide](docs/QUICKSTART.md).

## Running it on a Pi

Short version: flash the Arduino, plug it into the Pi over USB, split the Pi's audio between the speaker and the Arduino, then run `./scripts/deploy.sh` on the Pi. It sets everything up and starts the bear on boot.

The full walkthrough (wiring, firmware, Pi setup) is in the [Deployment guide](docs/DEPLOYMENT.md).

> The Arduino side is new and hasn't been tested on real hardware yet. Everything has been tested against the mock.

## The terminal menu

```bash
uv run raspi-ruxpin-cli
```

It runs the same services as the web app, without the web part. From the menu you can play a clip, speak some text, change the volume or sync mode, test the eyes and mouth, edit clip titles, and check how well your audio files will animate.

## Configuration

Settings come from environment variables in `.env`. Nested settings use a double underscore. Copy `.env.example.mac` or `.env.example.pi` to get started.

| Variable | What it does | Default |
|----------|--------------|---------|
| `PORT` | Web server port | `8888` |
| `SERIAL__PORT` | Arduino serial port | `/dev/ttyUSB0` |
| `SERIAL__USE_MOCK` | Use a fake Arduino (on by default on a Mac) | `false` on Linux |
| `SYNC__MODE` | `amplitude`, `phoneme`, or `realtime` | `amplitude` |
| `SYNC__SERVO_TYPE` | `hbridge` (original 5-wire) or `standard` (3-wire) | `hbridge` |
| `AUDIO__START_VOLUME` | Starting volume, 0–90 | `90` |
| `AUDIO__DEVICE` / `AUDIO__CARD_INDEX` / `AUDIO__MIXER` | ALSA sound card settings (Linux only) | system default |
| `TTS__ENGINE` | `espeak` or `piper` (Mac uses `say` for `espeak`) | `espeak` |
| `TTS__VOICE`, `TTS__SPEED`, `TTS__PITCH` | Voice tuning | see `.env.example` |
| `TTS__MAC_VOICE` | Voice for the Mac's `say` command (`say -v '?'` lists them) | `Fred` |

Volume is capped at 90%. Anything higher makes the Pi unstable.

Jaw positions live in `config/jaw_calibration.json`. See the [Deployment guide](docs/DEPLOYMENT.md#calibrating-the-mouth) for how that works.

## Project layout

```
raspi-ruxpin/
├── backend/
│   ├── main.py               # FastAPI app
│   ├── config.py             # Settings
│   ├── api/                  # WebSocket + health endpoints
│   ├── services/
│   │   └── bear_service.py   # Runs the show: audio, mouth sync, blinking
│   ├── hardware/
│   │   ├── arduino.py        # Serial link to the Arduino
│   │   ├── mock_serial.py    # Fake Arduino for Mac development
│   │   ├── audio_player.py   # Playback, volume, text-to-speech
│   │   ├── audio_analyzer.py # Amplitude and phoneme analysis
│   │   ├── timing_store.py   # Cached analysis results
│   │   └── calibration.py    # Mouth position table
│   ├── cli/                  # Terminal menu
│   ├── core/                 # Enums and exceptions
│   └── tests/
├── arduino/ruxpin/ruxpin.ino # Motor controller firmware
├── frontend/                 # Vue 3 + TypeScript + Vite
├── config/                   # Jaw calibration
├── data/
│   ├── sounds/               # examples/ (in the repo) and user/ (yours)
│   ├── timing/               # Analysis cache
│   └── tts/                  # Generated speech
├── docs/
└── .env.example{,.mac,.pi}
```

## Development

```bash
make dev           # backend with auto-reload
make frontend      # frontend dev server
make check         # lint + type check + tests
make help          # everything else
```

The backend uses `ruff` and `mypy` (strict). The frontend builds with `npm run build` inside `frontend/`.

## API

With the backend running:

- Web UI: http://localhost:5173 (dev server), or http://localhost:8888 once you've run `npm run build` and set `ENVIRONMENT=production`
- API docs: http://localhost:8888/docs
- Health: http://localhost:8888/api/health
- Status: http://localhost:8888/api/status

### WebSocket

Everything real-time goes through `/ws` as JSON.

**You send:**

```javascript
{ "type": "update_bear", "eyes": "open", "mouth": "closed" }
{ "type": "speak", "text": "Hello world" }
{ "type": "play", "sound": "starwars_iamyourfather" }
{ "type": "set_volume", "level": 75 }
{ "type": "set_blink_enabled", "enabled": true }
{ "type": "set_sync_mode", "mode": "amplitude" }   // amplitude | phoneme | realtime
{ "type": "set_character", "character": "teddy" }
{ "type": "analyze_audio", "sound": "starwars_iamyourfather" }
{ "type": "fetch_phrases" }
```

**You get back:**

```javascript
{ "type": "bear_state", "data": { "eyes": "open", "mouth_code": "C", "sync_mode": "amplitude", "volume": 75, ... } }  // 10 times a second
{ "type": "phrases", "data": { "phrase_key": "Title", ... } }
{ "type": "success", "message": "..." }
{ "type": "error", "message": "..." }
```

A bad message gets an `error` back and the connection stays open.

## Docs

- [Quick Start](docs/QUICKSTART.md): get running on your Mac
- [Deployment](docs/DEPLOYMENT.md): wiring, firmware, and Pi setup
- [Troubleshooting](docs/TROUBLESHOOTING.md): when things go sideways
- [Audio Files](docs/AUDIO_FILES.md): adding your own clips
- [Audio Guide](docs/audio-guide.md): making clips that animate well
- [Piper TTS](docs/PIPER_SETUP.md): nicer-sounding speech on the Pi

## Background

This started as a rebuild of the [C.H.I.P.py Ruxpin](https://www.hackster.io/chip/c-h-i-p-py-ruxpin-5f02f1) project from NextThing. There are build notes from the original on the [wiki](https://github.com/yamanote1138/raspi-ruxpin/wiki/), but some of them may predate the Arduino setup.

## License

MIT

## Version history

- **Next**: Motors now run from an Arduino over serial (no more Pi GPIO). Adds amplitude, phoneme, and realtime sync, a terminal menu, and audio quality scoring. Frontend reworked into a simpler two-column layout.
- **2.1.1**: Dependency updates and CI.
- **2.0.0** (2025): FastAPI + Vue 3 rewrite, WebSocket control, text-to-speech, Mac development mode.
- **1.0.0** (2023): Original Vue 2 + aiohttp version.
