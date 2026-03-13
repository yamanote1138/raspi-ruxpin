"""Audio quality scoring for mouth animation suitability.

Analyzes WAV files and produces a quality score (0–100) indicating how well
the audio will drive the bear's 7-position mouth model. Evaluates position
variety, activity balance, signal strength, and noise floor.
"""

import dataclasses
import math
import struct
import wave
from pathlib import Path

from backend.core.enums import MouthPosition
from backend.hardware.audio_analyzer import (
    POWER_COMPRESSION,
    WINDOW_MS,
    amplitude_to_position,
)

# Scoring lookup for position variety (how many of 7 positions are hit)
_VARIETY_SCORES: dict[int, int] = {
    7: 30,
    6: 28,
    5: 22,
    4: 15,
    3: 8,
    2: 3,
    1: 0,
}


@dataclasses.dataclass
class WavQualityReport:
    """Quality assessment of a WAV file for mouth animation.

    Attributes:
        score: Overall quality score (0–100).
        comments: Human-readable feedback lines.
        peak_amplitude: Max |sample| in 0.0–1.0 range (raw, before compression).
        rms_mean: Mean RMS across all analysis windows.
        noise_floor: Mean RMS of bottom-20% windows (proxy for silence level).
        snr_db: Signal-to-noise ratio in dB.
        position_variety: Number of unique mouth positions hit (1–7).
        activity_percent: Percentage of windows mapped to non-C positions.
        crest_factor_db: Peak-to-RMS ratio in dB.
        grade: Human-readable grade: Excellent / Good / Fair / Poor.
    """

    score: int
    comments: list[str]
    peak_amplitude: float
    rms_mean: float
    noise_floor: float
    snr_db: float
    position_variety: int
    activity_percent: float
    crest_factor_db: float
    grade: str


def analyze_wav_quality(path: Path) -> WavQualityReport:
    """Analyze a WAV file and produce a quality report for mouth animation.

    Reuses the same normalization, windowing, power compression, and threshold
    mapping as the amplitude analyzer to ensure consistent results.

    Args:
        path: Path to a WAV file.

    Returns:
        A WavQualityReport with score, grade, metrics, and comments.
    """
    # Read and normalize samples
    with wave.open(str(path), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    if sample_width == 2:
        num_samples = len(raw_data) // 2
        samples = list(struct.unpack(f"<{num_samples}h", raw_data))
        max_val = 32768.0
    elif sample_width == 1:
        samples = [s - 128 for s in raw_data]
        max_val = 128.0
    else:
        num_samples = len(raw_data) // 2
        samples = list(struct.unpack(f"<{num_samples}h", raw_data))
        max_val = 32768.0

    if n_channels > 1:
        samples = samples[::n_channels]

    # Compute peak amplitude (raw, before compression)
    peak_amplitude = max(abs(s / max_val) for s in samples) if samples else 0.0

    # Process windows — same logic as audio_analyzer
    window_samples = int(sample_rate * WINDOW_MS / 1000)
    rms_values: list[float] = []
    compressed_values: list[float] = []
    positions: list[MouthPosition] = []

    for i in range(0, len(samples), window_samples):
        chunk = samples[i : i + window_samples]
        if not chunk:
            break

        sum_sq = sum((s / max_val) ** 2 for s in chunk)
        rms = math.sqrt(sum_sq / len(chunk))
        rms_values.append(rms)

        compressed = rms**POWER_COMPRESSION if rms > 0 else 0.0
        compressed_values.append(compressed)

        positions.append(amplitude_to_position(compressed))

    if not rms_values:
        return WavQualityReport(
            score=0,
            comments=["File contains no audio data."],
            peak_amplitude=0.0,
            rms_mean=0.0,
            noise_floor=0.0,
            snr_db=0.0,
            position_variety=0,
            activity_percent=0.0,
            crest_factor_db=0.0,
            grade="Poor",
        )

    # Derive metrics
    rms_mean = sum(rms_values) / len(rms_values)

    # Noise floor: mean RMS of the quietest 20% of windows
    sorted_rms = sorted(rms_values)
    bottom_count = max(1, len(sorted_rms) // 5)
    noise_floor = sum(sorted_rms[:bottom_count]) / bottom_count

    # SNR
    if noise_floor > 0:
        snr_db = 20 * math.log10(rms_mean / noise_floor)
    else:
        snr_db = 60.0  # Effectively silent noise floor — excellent

    # Crest factor
    if rms_mean > 0:
        crest_factor_db = 20 * math.log10(peak_amplitude / rms_mean)
    else:
        crest_factor_db = 0.0

    # Position variety
    unique_positions = set(positions)
    position_variety = len(unique_positions)

    # Activity: percentage of non-C windows
    non_closed = sum(1 for p in positions if p != MouthPosition.C)
    activity_percent = (non_closed / len(positions)) * 100

    # --- Scoring ---
    # 1. Position variety (30 pts)
    variety_score = _VARIETY_SCORES.get(position_variety, 0)

    # 2. Activity balance (25 pts) — peak at 50–70%, penalize toward 0% or 100%
    activity_score = _score_activity(activity_percent)

    # 3. Signal strength (25 pts) — based on peak amplitude and mean RMS
    strength_score = _score_signal_strength(peak_amplitude, rms_mean)

    # 4. Noise floor (20 pts) — low noise + high SNR = good
    noise_score = _score_noise_floor(noise_floor, snr_db)

    total_score = variety_score + activity_score + strength_score + noise_score
    total_score = max(0, min(100, total_score))

    # Grade
    if total_score >= 85:
        grade = "Excellent"
    elif total_score >= 70:
        grade = "Good"
    elif total_score >= 50:
        grade = "Fair"
    else:
        grade = "Poor"

    # Comments
    comments = _generate_comments(
        variety_score=variety_score,
        activity_score=activity_score,
        strength_score=strength_score,
        noise_score=noise_score,
        position_variety=position_variety,
        activity_percent=activity_percent,
        peak_amplitude=peak_amplitude,
        noise_floor=noise_floor,
        snr_db=snr_db,
    )

    return WavQualityReport(
        score=total_score,
        comments=comments,
        peak_amplitude=peak_amplitude,
        rms_mean=rms_mean,
        noise_floor=noise_floor,
        snr_db=snr_db,
        position_variety=position_variety,
        activity_percent=activity_percent,
        crest_factor_db=crest_factor_db,
        grade=grade,
    )


def _score_activity(activity_percent: float) -> int:
    """Score activity balance (25 pts). Optimal range: 50–70%."""
    if 50 <= activity_percent <= 70:
        return 25
    if 30 <= activity_percent < 50:
        return 20
    if 70 < activity_percent <= 85:
        return 20
    if 20 <= activity_percent < 30:
        return 12
    if 85 < activity_percent <= 95:
        return 10
    if 10 <= activity_percent < 20:
        return 5
    if activity_percent > 95:
        return 3
    # Below 10%
    return 0


def _score_signal_strength(peak_amplitude: float, rms_mean: float) -> int:
    """Score signal strength (25 pts). Based on peak and mean RMS."""
    score = 0

    # Peak amplitude component (15 pts)
    if peak_amplitude >= 0.5:
        score += 15
    elif peak_amplitude >= 0.3:
        score += 12
    elif peak_amplitude >= 0.15:
        score += 7
    elif peak_amplitude >= 0.05:
        score += 3

    # Mean RMS component (10 pts)
    if rms_mean >= 0.05:
        score += 10
    elif rms_mean >= 0.02:
        score += 7
    elif rms_mean >= 0.01:
        score += 4
    elif rms_mean >= 0.005:
        score += 1

    return score


def _score_noise_floor(noise_floor: float, snr_db: float) -> int:
    """Score noise floor quality (20 pts). Low floor + high SNR = good."""
    score = 0

    # Noise floor component (10 pts)
    if noise_floor < 0.002:
        score += 10
    elif noise_floor < 0.005:
        score += 8
    elif noise_floor < 0.01:
        score += 5
    elif noise_floor < 0.02:
        score += 2

    # SNR component (10 pts)
    if snr_db >= 20:
        score += 10
    elif snr_db >= 15:
        score += 8
    elif snr_db >= 10:
        score += 5
    elif snr_db >= 5:
        score += 2

    return score


def _generate_comments(
    *,
    variety_score: int,
    activity_score: int,
    strength_score: int,
    noise_score: int,
    position_variety: int,
    activity_percent: float,
    peak_amplitude: float,
    noise_floor: float,
    snr_db: float,
) -> list[str]:
    """Generate human-readable feedback based on scoring components."""
    comments: list[str] = []

    # Position variety feedback
    if variety_score >= 28:
        comments.append(f"Great mouth variety — hits {position_variety} of 7 positions")
    elif variety_score >= 15:
        comments.append(f"Moderate variety — uses {position_variety} of 7 mouth positions")
    else:
        comments.append(
            f"Low variety — only {position_variety} of 7 positions used; "
            f"mouth movement will look repetitive"
        )

    # Activity feedback
    if activity_score >= 20:
        comments.append(f"Good activity balance ({activity_percent:.0f}% open)")
    elif activity_percent > 85:
        comments.append(
            f"Constant loud audio ({activity_percent:.0f}% open) — "
            f"mouth stays fully open with little variation"
        )
    elif activity_percent < 20:
        comments.append(
            f"Very quiet audio ({activity_percent:.0f}% open) — "
            f"mouth will barely move"
        )
    else:
        comments.append(f"Activity is outside ideal range ({activity_percent:.0f}% open)")

    # Signal strength feedback
    if strength_score >= 12:
        pass  # Good signal, no comment needed
    elif peak_amplitude < 0.15:
        comments.append(
            f"Audio is very quiet (peak {peak_amplitude:.3f}) — "
            f"consider normalizing to increase volume"
        )
    elif peak_amplitude < 0.3:
        comments.append(
            f"Audio is somewhat quiet (peak {peak_amplitude:.3f}) — "
            f"normalizing may improve animation"
        )

    # Noise floor feedback
    if noise_score >= 8:
        pass  # Clean audio, no comment needed
    elif noise_floor >= 0.01:
        comments.append(
            f"High noise floor ({noise_floor:.4f}) — "
            f"mouth may twitch during silent passages"
        )
    elif snr_db < 10:
        comments.append(
            f"Low signal-to-noise ratio ({snr_db:.1f} dB) — "
            f"silence/speech transitions will be muddy"
        )

    return comments
