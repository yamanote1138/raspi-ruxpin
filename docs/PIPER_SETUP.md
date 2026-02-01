# Piper TTS Setup Guide

Piper is a high-quality neural text-to-speech engine that provides much more natural-sounding voices than espeak.

## Why Piper on Raspberry Pi Only?

**macOS Issues:**
- Piper ships x86_64 binaries only (no ARM64/Apple Silicon support)
- Python `piper-tts` package missing `espeakbridge` C extension for macOS
- Would require building from source or complex Rosetta 2 setup

**Raspberry Pi:**
- ✅ Piper works natively on Linux ARM
- ✅ Much better voice quality than espeak
- ✅ Consistent behavior in production

## Installation on Raspberry Pi

### 1. Download Piper Binary

```bash
cd /home/pi/raspi-ruxpin
mkdir -p models/piper
cd models/piper

# For Raspberry Pi 3/4 (ARM 32-bit)
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_armv7l.tar.gz
tar -xzf piper_linux_armv7l.tar.gz
rm piper_linux_armv7l.tar.gz

# OR for Raspberry Pi 4/5 with 64-bit OS
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz
tar -xzf piper_linux_aarch64.tar.gz
rm piper_linux_aarch64.tar.gz
```

### 2. Download Voice Model

```bash
cd /home/pi/raspi-ruxpin/models

# High-quality US English male voice
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

**Alternative voices:**
- `en_US-amy-medium` - Female voice
- `en_US-joe-medium` - Male voice
- `en_GB-alan-medium` - British male

Browse all voices: https://rhasspy.github.io/piper-samples/

### 3. Update Configuration

Edit `.env`:

```bash
TTS__ENGINE=piper
TTS__VOICE=/home/pi/raspi-ruxpin/models/en_US-lessac-medium.onnx
```

### 4. Test Piper

```bash
echo "Hello, I am Piper. I like big butts and I cannot lie." | \
  ./models/piper/piper/piper \
  --model models/en_US-lessac-medium.onnx \
  --output_file test.wav

aplay test.wav
```

## Development on macOS

For local development on Mac, keep using espeak:

```bash
TTS__ENGINE=espeak
TTS__VOICE=en-us+m7
TTS__SPEED=140
TTS__PITCH=40
```

The voice quality won't match Piper, but it allows you to develop and test the application before deploying to the Pi.

## File Structure

```
raspi-ruxpin/
├── models/
│   ├── en_US-lessac-medium.onnx         # Voice model (60MB)
│   ├── en_US-lessac-medium.onnx.json    # Model config
│   └── piper/
│       ├── piper/
│       │   ├── piper                     # Main binary
│       │   ├── piper_phonemize          # Phoneme processor
│       │   ├── espeak-ng                # Phoneme engine
│       │   └── espeak-ng-data/          # Language data
│       └── ...
```

## Troubleshooting

### "Piper binary not found"

Make sure the binary is executable:
```bash
chmod +x models/piper/piper/piper
```

### "Model not found"

Verify paths in `.env`:
```bash
ls -l /home/pi/raspi-ruxpin/models/en_US-lessac-medium.onnx
```

### "Cannot load shared library"

Install dependencies:
```bash
sudo apt-get update
sudo apt-get install -y libgomp1 libatomic1
```

### Audio quality issues

Try different models or adjust speaking rate in the code (the audio_player already handles this properly).

## Python Library vs CLI

The application uses Piper as a **CLI tool** (subprocess), not the Python library, because:
- ✅ No compilation needed
- ✅ Works across platforms
- ✅ Avoids Python package dependencies
- ✅ Self-contained with bundled espeak-ng

## Performance

Piper generation takes ~2-3 seconds for a typical sentence on Raspberry Pi 4. This is cached, so repeated phrases are instant.
