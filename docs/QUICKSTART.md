# Quick Start

Get the bear running on your Mac, no hardware needed. A fake Arduino stands in for the real one, so you can play with everything except the actual servos.

Setting up the real thing? Skip to the [Deployment guide](DEPLOYMENT.md).

## What you need

- [uv](https://github.com/astral-sh/uv): `brew install uv` (or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Node.js](https://nodejs.org/) 20 or newer
- Python 3.12 or newer (uv will fetch one if you don't have it)

## Set it up

```bash
git clone https://github.com/yamanote1138/raspi-ruxpin.git
cd raspi-ruxpin

make install                 # Python and frontend dependencies
cp .env.example.mac .env
```

## Run it

You need two terminals.

```bash
# Terminal 1: backend on http://localhost:8888
make dev

# Terminal 2: frontend on http://localhost:5173
make frontend
```

Open http://localhost:5173.

## Try it out

- **Play a clip.** Pick one from the dropdown and hit play. The mouth on the bear picture should move along with the audio.
- **Speak some text.** Type something in the text box and hit speak. On a Mac this uses the built-in `say` voice.
- **Switch sync modes.** The sync button cycles through amplitude, realtime, and (if installed) phoneme. See below for what each one does.
- **Toggle the eyes, mouth, and blinking** with the buttons at the top of the controls.
- **Click the info button** to see what the backend thinks is going on: platform, TTS engine, how many clips it found, and whether phoneme mode is available.

Audio plays through your Mac's speakers at the current system volume, so check that before you hit play.

### The three sync modes

- **Amplitude** is the default. The backend measures how loud the clip is, ahead of time, and sends timed mouth commands.
- **Realtime** has the Arduino listening to the audio and reacting live. On a Mac the mock Arduino fakes this, so you'll see the mouth move but it isn't a real test of the hardware.
- **Phoneme** works out mouth shapes from the actual sounds in the speech. It needs extra packages (below).

### Turning on phoneme mode (optional)

```bash
brew install espeak-ng
uv pip install -e '.[phoneme]'
```

The first time you use it, Whisper downloads a small speech model, so expect a pause. After that, results are cached in `data/timing/`.

If the sync button skips phoneme, the packages aren't installed. The info button will tell you what's missing.

## Use the terminal menu instead

```bash
uv run raspi-ruxpin-cli
```

Same bear, no browser. Press a letter to pick an option: play a clip, speak text, manage sound files, or open settings. Esc goes back.

## Add your own clips

Drop WAV files into `data/sounds/user/`. They show up in the dropdown after a restart. See [Audio Files](AUDIO_FILES.md) for the format and how to convert things, and [Audio Guide](audio-guide.md) for making clips that animate well.

## Production build

To serve the UI straight from the backend (this is how it runs on a Pi), build it and turn on production mode:

```bash
cd frontend && npm run build && cd ..
ENVIRONMENT=production make run
```

Then open http://localhost:8888. Without `ENVIRONMENT=production` the backend won't serve the built UI, and you'll get a blank page.

## Run the checks

```bash
make check        # ruff + mypy + pytest
```

## If something's off

- **The page says disconnected.** Make sure `make dev` is running. The frontend expects the backend on port 8888.
- **Port 8888 is taken.** Change `PORT` in `.env`. If you're using the dev server, update the proxy in `frontend/vite.config.ts` to match.
- **No sound.** Check your system volume and output device. Playback uses `afplay`.
- **Phoneme mode is missing.** Install the extras above.

More in [Troubleshooting](TROUBLESHOOTING.md).
