# Troubleshooting

When things go sideways. Find the symptom, try the fixes in order.

**Contents**

- [The service won't start](#the-service-wont-start)
- [I can't reach the web page](#i-cant-reach-the-web-page)
- [The Arduino won't connect](#the-arduino-wont-connect)
- [The bear connects but doesn't move right](#the-bear-connects-but-doesnt-move-right)
- [The mouth is out of sync or looks wrong](#the-mouth-is-out-of-sync-or-looks-wrong)
- [Audio problems](#audio-problems)
- [Text-to-speech problems](#text-to-speech-problems)
- [Phoneme mode isn't available](#phoneme-mode-isnt-available)
- [Development problems](#development-problems)
- [Slow on the Pi](#slow-on-the-pi)
- [Getting help](#getting-help)

---

## The service won't start

If you're running the backend as a systemd service (the deploy script sets this up):

```bash
sudo systemctl status raspi-ruxpin
sudo journalctl -u raspi-ruxpin -n 50
```

The last lines of the log usually say what went wrong. Common causes:

- **The Arduino won't connect.** See [that section](#the-arduino-wont-connect). Note that a service running as your user needs you to be in the `dialout` group, and group changes only apply after you log out and back in.
- **Something else has the serial port.** If you ran the backend or the terminal menu by hand, stop it first, or stop the service before testing by hand: `sudo systemctl stop raspi-ruxpin`.
- **A bad `.env`.** Comments have to be on their own lines. The service doesn't understand a `#` after a value.
- **The service file has the wrong user or folder.** Rerun `./scripts/setup-service.sh` from the project folder. It fills those in.
- **The `data/` folder isn't writable** by the user the service runs as. Check with `ls -ld data`.

Then try running it by hand to see the error directly (stop the service first): `uv run python -m backend.main`.

---

## I can't reach the web page

**Is the backend running?**

```bash
curl http://localhost:8888/api/health
```

You should get back `{"status":"ok", ...}`. If not, start it (`make run`, or `make dev` while developing) and read what it prints.

**Are you using the right address and port?** The backend listens on port **8888** (change it with `PORT` in `.env`). From another device, use the Pi's address, not `localhost`. Find it with `hostname -I`.

**The page loads but says disconnected.** The page talks to the backend over a WebSocket at `/ws`. If you're running the frontend dev server on port 5173, the backend still has to be up on 8888. The dev server passes requests through to it.

**A blank page or "not found" from the backend on port 8888.** The backend only serves the web UI when two things are true: the frontend has been built, and `ENVIRONMENT=production` is set in `.env`. Run:

```bash
cd frontend && npm run build
```

Set `ENVIRONMENT=production` (the Pi example file already does), restart the backend, and reload. While developing, skip all this and use the dev server on port 5173.

**Can't connect from another device.** Check that a firewall isn't blocking port 8888. On a Pi with `ufw`: `sudo ufw allow 8888/tcp`.

---

## The Arduino won't connect

Start by looking at the top of the backend's output. These are the messages to look for:

| Message | What it usually means |
|---------|-----------------------|
| `Failed to connect to Arduino: ...` | Wrong port, or no permission to open it |
| `Arduino did not send READY within 10.0s` | The port opened, but the Arduino isn't answering |
| `Arduino did not acknowledge configuration` | The Arduino answered, then choked during setup |
| `Failed to start BearService` | Wraps one of the above. Look just before it |

### 1. Is it the right port?

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Unplug the Arduino, run it again, plug it back in, and run it once more. The one that appears is yours. Set it in `.env`:

```bash
SERIAL__PORT=/dev/ttyACM0
```

On a Mac the mock Arduino kicks in on its own, so `SERIAL__PORT` doesn't matter there unless you set `SERIAL__USE_MOCK=false`.

### 2. Permission denied

Your user has to be in the `dialout` group to open serial ports on Linux:

```bash
sudo usermod -a -G dialout $USER
```

Log out and back in. Check with `groups`.

### 3. Something else has the port

Only one program can talk to the Arduino at a time. Close the Arduino IDE's Serial Monitor, and make sure you don't have a second copy of the backend or the CLI running:

```bash
ps aux | grep -E 'backend.main|raspi-ruxpin'
```

### 4. Is the firmware on it?

An Arduino with no firmware, or the wrong one, never says `READY`. Reflash `arduino/ruxpin/ruxpin.ino` (see the [Deployment guide](DEPLOYMENT.md#flash-the-arduino)). The baud rate is 115200 on both sides, so if you changed it in one place, change it in the other.

To listen for yourself, open the Arduino IDE's Serial Monitor at 115200 baud, press the Arduino's reset button, and look for `READY`. Close the monitor afterward so the backend can use the port.

### 5. Is the mock turned on by accident?

The web UI's info button shows the connection type. If it says `mock` on a Pi, check `.env`:

```bash
SERIAL__USE_MOCK=false
```

### 6. A bad cable

Charge-only USB cables exist, and they look identical to good ones. If the port never shows up in step 1, try a different cable.

---

## The bear connects but doesn't move right

First, take the web app and audio out of the picture. Use the terminal menu:

```bash
uv run raspi-ruxpin-cli
```

Go to **Settings**, then **Test eyes** and **Test mouth positions**. That sends commands straight to the Arduino.

**Nothing moves at all.**
- Check motor power. Motors need their own supply, not the Arduino's 5V pin, and all the grounds need to be connected.
- Check that `SYNC__SERVO_TYPE` matches what you wired: `hbridge` for the original 5-wire mechanism, `standard` for 3-wire hobby servos.
- Check the pins against the [wiring table](DEPLOYMENT.md#wiring).

**A motor runs backward.** For H-bridge motors, swap the two direction wires (for example, pins 4 and 5 for the upper jaw).

**The mouth doesn't open far enough (or opens too far).** Adjust the numbers in `config/jaw_calibration.json` and restart the backend. See [Calibrating the mouth](DEPLOYMENT.md#calibrating-the-mouth).

**The eyes never blink.** Blinking can be turned off. Check the blink button.

**"Bear is busy".** It's still playing or speaking. Wait for it to finish.

---

## The mouth is out of sync or looks wrong

Figure out which sync mode you're in (the sync button shows it), then look below.

### Amplitude mode

The backend measures the clip's loudness ahead of time. It works best on clean audio with natural ups and downs.

- **Score the clip.** In the terminal menu: **Manage sound files**, then **Audio quality analysis**. Anything scoring Poor or Fair will animate badly. The [Audio Guide](audio-guide.md) explains how to fix that.
- **The mouth barely moves.** The clip is too quiet. Normalize it.
- **The mouth is stuck wide open.** The clip is too loud or clipped.
- **The mouth twitches during pauses.** Background noise. Clean it up.

### The mouth looks wrong after a code or settings change

Analysis results are saved in `data/timing/` and reused. If you replace a clip, the backend notices that the audio is newer than the saved result and re-analyzes it. It can't tell if you changed how the analysis itself works, though. In that case, clear the saved results:

```bash
rm data/timing/*.csv
```

It's always safe to delete files in `data/timing/`. They just get rebuilt the next time each clip plays.

### Realtime mode

The Arduino listens to the audio on pin `A0`.

- Make sure the audio actually reaches `A0`, and that the grounds are shared.
- The input has to be centered around 2.5V. See [the audio input](DEPLOYMENT.md#the-audio-input).
- Turn the volume up or down. Too quiet and the mouth stays shut. Too loud and it's stuck open.
- Switch to amplitude mode. If that looks right and realtime doesn't, the problem is in the audio input circuit, not the software.

### Phoneme mode

If the shapes look off, try amplitude mode on the same clip to compare. Phoneme mode depends on Whisper understanding the speech. Mumbly, noisy, or music-heavy clips can trip it up.

---

## Audio problems

### No sound

**On a Pi:**

```bash
aplay -l                  # is there a sound card?
speaker-test -t wav -c 2  # can it play anything? (Ctrl+C to stop)
amixer scontrols          # what volume controls exist?
```

- If `speaker-test` is silent, this isn't a Ruxpin problem. Check cables and `raspi-config` (System Options, then Audio).
- If it plays on the wrong output, set `AUDIO__DEVICE` and `AUDIO__CARD_INDEX` in `.env`. See [Audio](DEPLOYMENT.md#audio).
- If the volume control name isn't `PCM`, set `AUDIO__MIXER` to one of the names `amixer scontrols` printed (`Master` and `Speaker` are common).

**On a Mac:** playback goes through `afplay` at the system volume. Check your output device and volume.

### Too quiet

Both the system volume and the app volume matter. In `alsamixer`, raise the volume on your card. The app's volume slider stops at 90%.

### "Volume must be between 0 and 90"

That's the safety cap. Anything above 90% makes the Pi unstable, so it's refused on purpose.

### "Audio file not found"

The clip name doesn't match a file in `data/sounds/examples/` or `data/sounds/user/`. Clips are found when the backend starts, so restart it after adding files.

### Stuttering audio

Usually the Pi is overloaded. See [Slow on the Pi](#slow-on-the-pi).

---

## Text-to-speech problems

| Message | Fix |
|---------|-----|
| `TTS engine 'espeak' not found` | `sudo apt install espeak-ng`. If the `espeak` command still isn't there, `sudo apt install espeak` |
| `espeak failed: ...` | Usually a bad voice name. Check `TTS__VOICE` in `.env` (for example `en-us+m7`) |
| `say failed: ...` | Mac only. The Mac voice comes from `TTS__MAC_VOICE` (default `Fred`) and ignores `TTS__VOICE`. See what's installed with `say -v '?'` |
| `Piper binary not found` / `Piper model not found: ...` | Follow the [Piper setup guide](PIPER_SETUP.md), or set `TTS__ENGINE=espeak` |

Generated speech is saved in `data/tts/` and reused. Changing the voice, speed, or pitch gets you fresh speech automatically. It's safe to delete the folder's contents.

---

## Phoneme mode isn't available

The sync button skips phoneme mode, or you see:

```
Phoneme mode unavailable: Missing Python packages: faster-whisper, phonemizer
```

Install the extras:

```bash
uv pip install -e '.[phoneme]'
```

You also need the espeak-ng program and library: `brew install espeak-ng` on a Mac, `sudo apt install espeak-ng` on a Pi. The first run downloads a Whisper model, so it needs internet access once.

---

## Development problems

**Frontend changes don't show up.** Are you looking at the right port? The dev server (5173) shows changes right away. The backend's own page (8888) shows the *last build*, so run `npm run build` again.

**Backend changes don't show up.** Use `make dev`, which restarts on changes. `make run` doesn't.

**Type errors after pulling.** Run `uv sync --extra dev` so your tools match the lockfile.

---

## Slow on the Pi

- **The web page is laggy.** A Pi 3 is fine for the bear but slow at everything else. A Pi 4 or 5 is comfortable.
- **The first play of a clip is slow.** That's the analysis. Amplitude analysis is quick. Phoneme analysis (Whisper) is slow on a Pi, but it only happens once per clip. After that the result comes from `data/timing/`.
- **Check what's eating the CPU:**

  ```bash
  top
  ```

- **Low on memory:** `free -h`. Whisper is the hungry one.

---

## Getting help

Before asking, grab these:

1. **What version and where:** `curl http://localhost:8888/api/status`
2. **The log.** Turn on more detail by setting `DEBUG=true` in `.env` and restarting. Serial traffic (`TX:` lines) shows up at debug level.
   - The backend logs to the terminal it runs in.
   - The terminal menu logs to `data/logs/cli.log`.
3. **The info button** in the web UI: platform, TTS engine, connection type, and clip count in one place.
4. **What you expected, and what happened instead.**

Then open an issue at https://github.com/yamanote1138/raspi-ruxpin/issues.

## Quick reference

```bash
# Is it up?
curl http://localhost:8888/api/health

# Serial ports
ls /dev/ttyUSB* /dev/ttyACM*
groups                       # should include dialout

# Audio (Linux)
aplay -l
amixer scontrols
speaker-test -t wav -c 2

# Terminal menu (talks to the Arduino directly)
uv run raspi-ruxpin-cli

# Checks
make check
```

**Files worth knowing:** `.env` (settings), `config/jaw_calibration.json` (mouth positions), `data/timing/` (saved analysis), `data/tts/` (generated speech), `data/logs/cli.log` (terminal menu log).
