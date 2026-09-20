# Deployment Guide

How to build the real thing: an Arduino running the motors, a Raspberry Pi running everything else.

> **Heads up:** the Arduino setup is new and hasn't been tested on real hardware yet. The software has been tested against a mock Arduino, so the serial protocol, the analysis, and the web app are solid. The wiring and firmware are the parts still waiting on a real bear. If something here doesn't match reality, trust reality and please fix the doc.

## What you need

- Raspberry Pi 3, 4, or 5 running Raspberry Pi OS
- An Arduino with a USB port (an Uno or Nano works; it needs the `Servo` library, PWM pins, and an analog input)
- USB cable from the Arduino to the Pi
- A Teddy Ruxpin with working motors, or standard 3-wire hobby servos
- An H-bridge motor driver for each motor, if you're using the original 5-wire mechanism
- A speaker
- An audio Y-splitter or similar, so the Pi's audio can go to both the speaker and the Arduino

## How the pieces connect

```
 Pi ── USB ─────────────────────► Arduino ──► eyes + mouth motors
  │                                  ▲
  └── audio out ──┬──► speaker       │ A0 (realtime mode only)
                  └──────────────────┘
```

- **USB** carries the commands (and the mouth reports coming back in realtime mode).
- **Audio** goes to the speaker for people to hear, and to the Arduino's `A0` pin so it can react live. If you only use amplitude or phoneme mode you can skip the connection to `A0`, because the Pi already knows what the mouth should do.

## Wiring

These pins come from the firmware (`arduino/ruxpin/ruxpin.ino`).

| Part | PWM / signal | Direction | Reverse direction |
|------|:------------:|:---------:|:-----------------:|
| Upper jaw | 9 | 4 | 5 |
| Lower jaw | 10 | 6 | 7 |
| Eyes | 11 | 12 | 13 |
| Audio in | A0 | | |

- **H-bridge (original 5-wire mechanism):** all three pins per motor are used. Set `SYNC__SERVO_TYPE=hbridge`.
- **Standard 3-wire servos:** only the signal pin (9, 10, 11) is used. Set `SYNC__SERVO_TYPE=standard`.

Give the motors their own power supply. Don't run them off the Arduino's 5V pin, and tie all the grounds together (Arduino, motor supply, Pi audio ground).

### The audio input

The firmware reads `A0` as a signal that swings around the middle of the Arduino's range (about 2.5V). Audio straight from a Pi swings around 0V, so it needs a little circuit in front of `A0` to shift it up. A capacitor plus two equal resistors forming a voltage divider is the usual trick.

The exact parts haven't been settled yet. Once you've got a version that works, add it here.

## Flash the Arduino

1. Open `arduino/ruxpin/ruxpin.ino` in the [Arduino IDE](https://www.arduino.cc/en/software).
2. Pick your board and port.
3. Upload.

After a reset the Arduino waits for the Pi. When the backend connects, it does this:

1. The Arduino says `READY`.
2. The Pi sends the servo type, the position table for the mouth, and the sync mode.
3. The Arduino answers `OK` and starts running.

That means you don't reflash to change the servo type, the calibration, or the sync mode. Change the setting on the Pi and restart it.

## Set up the Pi

There are two ways to do this. The deploy script does everything below in one go. The manual steps let you see (and control) each piece.

### The quick way: the deploy script

```bash
git clone https://github.com/yamanote1138/raspi-ruxpin.git
cd raspi-ruxpin
./scripts/deploy.sh
```

It creates `.env` from the Pi template (and opens it for you to check the serial port), installs system packages and uv, installs the Python dependencies, builds the frontend, adds you to the `dialout` group, helps you pick a sound card, and installs and starts the systemd service so the bear starts on boot.

Log out and back in afterward if it added you to a group. To update later, run `./scripts/deploy.sh --update`.

The script is new for the Arduino setup and hasn't been run on a real Pi yet. If it trips, the manual steps below show what each piece is supposed to do.

### The manual way

#### 1. System packages

```bash
sudo apt update
sudo apt install -y python3-dev libasound2-dev alsa-utils espeak-ng git
```

You also need Node.js 20 or newer to build the frontend. The [NodeSource instructions](https://github.com/nodesource/distributions) are the easiest way.

#### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new shell afterward so `uv` is on your path.

#### 3. Get the code

```bash
git clone https://github.com/yamanote1138/raspi-ruxpin.git
cd raspi-ruxpin
```

#### 4. Install dependencies and build the frontend

```bash
make install-pi
cd frontend && npm install && npm run build && cd ..
```

That installs the Pi extras (ALSA and Piper) and builds the web UI. The backend serves the built UI itself, so you don't need the dev server.

Want phoneme mode? Add the extra packages too:

```bash
uv pip install -e '.[phoneme]'
```

Whisper can be slow on a Pi. The first analysis of each clip takes a while, but the result is cached in `data/timing/`, so it only happens once per clip.

#### 5. Find the Arduino's port

Plug it in, then:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Genuine Uno boards usually show up as `/dev/ttyACM0`. Nano clones with a CH340 chip usually show up as `/dev/ttyUSB0`.

Your user needs permission to open it:

```bash
sudo usermod -a -G dialout $USER
```

Log out and back in (or reboot) for that to take effect.

#### 6. Configure

```bash
cp .env.example.pi .env
nano .env
```

The settings you're most likely to change:

```bash
SERIAL__PORT=/dev/ttyUSB0
SERIAL__USE_MOCK=false
SYNC__SERVO_TYPE=hbridge
SYNC__MODE=amplitude
AUDIO__START_VOLUME=90
```

Set `SERIAL__PORT` to whatever you found in the last step. `SYNC__SERVO_TYPE` is `hbridge` or `standard`. `SYNC__MODE` is `amplitude`, `phoneme`, or `realtime`. 90 is the highest volume allowed.

Keep comments on their own lines in `.env`. The systemd service reads this file too, and it doesn't understand a `#` comment after a value.

The full list is in the [README](../README.md#configuration).

#### 7. Test run

```bash
uv run python -m backend.main
```

Look for the Arduino connecting in the log. If it stalls, jump to [Troubleshooting](TROUBLESHOOTING.md#the-arduino-wont-connect).

Then open `http://<your-pi-address>:8888` from another device. Find the Pi's address with `hostname -I`. You can also check that the backend is up:

```bash
curl http://localhost:8888/api/health
```

Press Ctrl+C to stop.

## Starting on boot

The deploy script installs this for you. To install just the service (for example, if you set everything up by hand):

```bash
./scripts/setup-service.sh
```

It fills in your username and folder, installs `raspi-ruxpin.service`, and starts it. The service runs as your user with access to the serial port and sound card, and it can only write to the `data/` folder (plus `~/.cache`, where the Whisper speech model lives).

```bash
sudo systemctl status raspi-ruxpin      # is it running?
sudo journalctl -u raspi-ruxpin -f      # watch the log
sudo systemctl restart raspi-ruxpin     # after changing .env or calibration
sudo systemctl stop raspi-ruxpin        # stop it (do this before testing by hand)
```

Only one thing can use the Arduino's serial port at a time, so stop the service before running the backend or the terminal menu yourself.

## Calibrating the mouth

The mouth has seven positions:

| Code | Meaning | Sounds like |
|:----:|---------|-------------|
| C | Closed | silence |
| T | Teeth together | t, d, s, z, n, l |
| S | Slightly open | th, sh, ch, j |
| N | Neutral | short vowels |
| M | Medium open | eh, ae |
| L | Large open | ah, aw |
| W | Wide open | aa, ow |

Each one has an upper and lower jaw value in `config/jaw_calibration.json`:

```json
{
  "C": {"upper": 101, "lower": 99},
  "W": {"upper": 55,  "lower": 53}
}
```

(The real file lists all seven.) For standard servos these are angles in degrees. For H-bridge motors they're power levels, as a percentage.

Edit the file, then restart the backend (`sudo systemctl restart raspi-ruxpin` if it's running as a service). It sends the table to the Arduino every time it connects.

To see what your numbers actually do, use the terminal menu. In **Settings**, choose **Test mouth positions** and it steps through all seven.

```bash
uv run raspi-ruxpin-cli
```

## Audio

### Pick the right sound card

```bash
aplay -l                  # list sound cards
amixer scontrols          # list volume controls
speaker-test -t wav -c 2  # play a test sound (Ctrl+C to stop)
```

If the default output isn't the one you want, set these in `.env`:

```bash
AUDIO__DEVICE=plughw:1,0   # card 1, device 0
AUDIO__CARD_INDEX=1        # same card, for the volume control
AUDIO__MIXER=PCM           # PCM, Master, or Speaker
```

### Volume

The volume is capped at 90%. Going higher makes the Pi unstable, so the backend refuses it.

### Nicer speech

The default voice is espeak, which sounds like a robot. For something closer to a person, see the [Piper setup guide](PIPER_SETUP.md).

## Updating

```bash
cd raspi-ruxpin
./scripts/deploy.sh --update
```

That stops the service, pulls the latest code, reinstalls dependencies, rebuilds the frontend, and starts the service again. If the firmware changed, reflash the Arduino too.

By hand, that's `git pull`, `make install-pi`, then `cd frontend && npm install && npm run build`, then a restart.

## Backing up

The bits that are yours:

```bash
tar czf ruxpin-backup.tar.gz .env config/ data/sounds/user/
```

## Reaching it from other devices

Once it's running, anything on your network can use `http://<pi-address>:8888`. If you'd like the address to stay put, reserve it for the Pi in your router's settings.

There's no login. Don't expose port 8888 to the internet.

## Not covered yet

Servo timing, the audio input circuit, and realtime-mode tuning all need a session with a real bear. This guide will get those sections once they've been through one.

Something not working? See [Troubleshooting](TROUBLESHOOTING.md).
