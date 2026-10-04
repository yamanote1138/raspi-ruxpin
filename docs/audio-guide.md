# Audio Preparation Guide

How to prepare audio files that produce the best mouth animation on Raspi Ruxpin.

## Ideal Format

| Property    | Recommended         |
|-------------|---------------------|
| Format      | WAV (PCM)           |
| Channels    | Mono                |
| Bit depth   | 16-bit              |
| Sample rate | 22050 Hz or 16000 Hz |

Stereo files will work (only the first channel is used), but mono is preferred. Other sample rates are accepted but may produce slightly different timing characteristics.

## Volume and Loudness

The amplitude analyzer maps audio volume to 7 mouth positions. Getting the levels right is critical:

- **Peak amplitude**: Aim for 0.5–0.9. This gives the analyzer enough headroom to distinguish all 7 positions.
- **Mean RMS**: Target 0.05–0.15 (before power compression). This ensures there's enough signal to drive varied mouth movement.
- **Too quiet** (peak < 0.15): The mouth will barely open — most windows map to Closed (C) or Teeth (T).
- **Too loud / clipped** (peak at 1.0, flat waveform): The mouth stays stuck wide open (W) with no variation.

### Normalizing in Audacity

1. Open the WAV file in Audacity
2. Select All (Ctrl+A / Cmd+A)
3. Effect → Normalize
4. Set peak amplitude to **-3 dB** (about 0.7 on the 0–1 scale)
5. Check "Remove DC offset"
6. Export as WAV: 16-bit PCM, mono

## Dynamic Range

Natural speech has pauses, whispers, and emphasis — this is exactly what produces lively mouth animation. The analyzer uses power compression (exponent 0.7) to expand quiet sounds, but it still needs real variation in the source.

- **Good**: Narration, storytelling, conversational speech — natural volume changes produce 5–7 mouth positions.
- **Bad**: Heavily compressed or limited audio (podcasts with aggressive processing, radio broadcast audio) — the mouth tends to sit at one or two positions.
- **Ideal activity**: 30–85% of analysis windows should map to a non-Closed position. Below 20% means the audio is too quiet; above 95% means it's constant loud sound.

## Noise Floor

Background noise confuses the silence detection. When noise is loud enough to cross the lowest threshold, the mouth twitches during pauses instead of staying cleanly closed.

- **Target**: Silence-window RMS below 0.005
- **Acceptable**: Below 0.01
- **Problematic**: Above 0.01 — the Closed/Teeth boundary gets muddy

### Reducing Noise in Audacity

1. Select a section of pure silence (no speech)
2. Effect → Noise Reduction → Get Noise Profile
3. Select All (Ctrl+A / Cmd+A)
4. Effect → Noise Reduction → reduce by 12–18 dB
5. Preview to make sure speech isn't distorted

## Quality Score

The CLI's "Check file format" tool scores each file on a 0–100 scale across four components:

| Component          | Points | What it measures                                      |
|--------------------|--------|-------------------------------------------------------|
| Position variety   | 30     | How many of the 7 mouth positions are actually used   |
| Activity balance   | 25     | Whether open-time % falls in the ideal 30–85% range   |
| Signal strength    | 25     | Peak amplitude and mean RMS — is there enough signal? |
| Noise floor        | 20     | How clean the silence is, and signal-to-noise ratio   |

**Grades:**

| Grade     | Score  | Meaning                                        |
|-----------|--------|------------------------------------------------|
| Excellent | 85–100 | Great animation — varied, lively mouth movement |
| Good      | 70–84  | Solid results, minor improvements possible      |
| Fair      | 50–69  | Usable but animation quality is noticeably limited |
| Poor      | 0–49   | Significant issues — consider re-recording or processing |

## Quick Checklist

- [ ] WAV format, mono, 16-bit, 22050 or 16000 Hz
- [ ] Peak amplitude between 0.5 and 0.9 (normalize if needed)
- [ ] Natural dynamic range preserved (avoid heavy compression)
- [ ] Clean background — minimal hiss, hum, or room noise
- [ ] Run the quality scan in the CLI to verify your score

## Export Settings (Audacity)

File → Export Audio:
- **Format**: WAV (Microsoft)
- **Encoding**: Signed 16-bit PCM
- **Sample Rate**: 22050 Hz
- **Channels**: Mono

For files recorded at other sample rates, use Tracks → Resample to 22050 Hz before exporting.
