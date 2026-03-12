# Audio Files

Raspi Ruxpin plays WAV audio files with synchronized mouth movement. This guide explains how to prepare and add your own audio clips.

## Directory Structure

```
data/sounds/
├── examples/    # Included in repo — sample clips for testing
└── user/        # Your clips — gitignored, not committed
```

Files in `examples/` ship with the repo. Place your own files in `user/`. Both directories are searched automatically when playing a sound by name.

## Audio Format

The system accepts standard WAV files. For best results:

| Parameter   | Recommended | Notes                                    |
|-------------|-------------|------------------------------------------|
| Format      | WAV (PCM)   | Uncompressed — required by the analyzer  |
| Channels    | 1 (mono)    | Stereo works but wastes space            |
| Sample rate | 22050 Hz    | 16000–44100 Hz all work fine             |
| Bit depth   | 16-bit      | Signed integer (standard PCM)            |
| Codec       | PCM         | No compression (no MP3, AAC, OGG, etc.)  |

The amplitude and phoneme analyzers read the sample rate from the file header, so any rate works. Mono 16-bit 22050 Hz is the sweet spot between quality and file size.

## Converting Audio

### Using ffmpeg (recommended)

Convert any audio file to the correct format:

```bash
ffmpeg -i input.mp3 -ac 1 -ar 22050 -sample_fmt s16 output.wav
```

Flags:
- `-ac 1` — mono
- `-ar 22050` — 22050 Hz sample rate
- `-sample_fmt s16` — 16-bit signed PCM

### Using Audacity

1. Open your audio file
2. **Tracks > Mix > Mix Stereo Down to Mono** (if stereo)
3. **Project Rate** (bottom-left): set to 22050
4. **File > Export Audio**
   - Format: WAV (Microsoft)
   - Encoding: Signed 16-bit PCM

### Using macOS afconvert

```bash
afconvert -f WAVE -d LEI16 -c 1 -r 22050 input.aiff output.wav
```

## Naming Convention

Sound files are referenced by their stem name (filename without `.wav`). Use lowercase with underscores:

```
moviename_quotename.wav
```

Examples: `caddyshack_goinforme.wav`, `starwars_iamyourfather.wav`

## Sound Titles

Titles are read from WAV file metadata — specifically the ID3 `TIT2` tag. Files without an embedded title fall back to the filename stem as the display name.

To set or update titles, use the CLI's **"Manage sound titles"** option, which writes the `TIT2` tag directly into the WAV file.

## Trimming Silence

Clips with long leading silence will delay mouth movement. Trim silence from the start:

```bash
ffmpeg -i input.wav -af "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-40dB" -ac 1 -ar 22050 -sample_fmt s16 output.wav
```

## File Size

A typical 5-second mono 22050 Hz 16-bit clip is about 220 KB. Keep clips short (under 30 seconds) for responsive playback on the Pi.
