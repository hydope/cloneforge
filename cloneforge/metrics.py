"""Measured metrics. Every function here computes a number from real audio
or real text — or the caller must report NOT MEASURED. Nothing in this
module estimates, guesses, or hard-codes a quality score.
"""

from __future__ import annotations

import math
import subprocess
import wave
from contextlib import closing
from pathlib import Path


def wav_duration_seconds(path: str | Path) -> float:
    """Duration of a WAV file from its header (exact, no decoding)."""
    with closing(wave.open(str(path), "rb")) as w:
        frames = w.getnframes()
        rate = w.getframerate()
    if rate == 0:
        raise ValueError(f"zero sample rate in {path}")
    return frames / float(rate)


def media_duration_seconds(path: str | Path) -> float:
    """Duration of any media file via ffprobe; WAVs use the exact header path."""
    if Path(path).suffix.lower() == ".wav":
        return wav_duration_seconds(path)
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def duration_ratio(reference_s: float, generated_s: float) -> float:
    """1.0 = generated audio is exactly as long as the reference.

    Used as a pace proxy only when both clips speak comparable word counts;
    for same-line comparisons prefer speech-rate difference.
    """
    if reference_s <= 0:
        raise ValueError("reference duration must be > 0")
    return generated_s / reference_s


def speech_rate_wpm(word_count: int, duration_s: float) -> float:
    """Words per minute."""
    if duration_s <= 0:
        raise ValueError("duration must be > 0")
    return word_count / (duration_s / 60.0)


def rate_difference_pct(reference_wpm: float, generated_wpm: float) -> float:
    """Signed % difference in speaking rate; 0.0 = identical pace."""
    if reference_wpm <= 0:
        raise ValueError("reference rate must be > 0")
    return (generated_wpm - reference_wpm) / reference_wpm * 100.0


def _edit_distance(a: list[str], b: list[str]) -> int:
    """Levenshtein distance over token lists."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, tok_a in enumerate(a, start=1):
        current = [i]
        for j, tok_b in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,                # deletion
                current[j - 1] + 1,             # insertion
                previous[j - 1] + (tok_a != tok_b),  # substitution
            ))
        previous = current
    return previous[-1]


def wer(reference_text: str, hypothesis_text: str) -> float:
    """Word error rate in percent: (S + D + I) / N * 100.

    Case-insensitive, punctuation-stripped. Returns 0.0 for two empty
    strings; raises on an empty reference with a non-empty hypothesis
    is impossible to score honestly, so it returns 100.0 * len(hyp words)
    capped by the caller — no: it raises ValueError. Callers must handle
    an empty reference explicitly instead of receiving a fake number.
    """
    ref = _tokens(reference_text)
    hyp = _tokens(hypothesis_text)
    if not ref:
        raise ValueError("WER needs a non-empty reference text")
    return _edit_distance(ref, hyp) / len(ref) * 100.0


def _tokens(text: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text)
    return cleaned.split()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two embedding vectors, in [-1, 1]."""
    if len(a) != len(b) or not a:
        raise ValueError("vectors must be non-empty and equal length")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        raise ValueError("zero vector has no direction")
    return dot / (na * nb)


def median_f0_hz(samples: list[float], sample_rate: int,
                 min_hz: float = 50.0, max_hz: float = 400.0) -> float | None:
    """Median fundamental frequency via autocorrelation over voiced frames.

    Pure-numpy implementation. Returns None when no voiced frame is found —
    callers must treat None as NOT MEASURED, never as 0 Hz.
    """
    import numpy as np

    x = np.asarray(samples, dtype=np.float64)
    if x.size == 0 or sample_rate <= 0:
        return None
    frame = int(sample_rate * 0.04)  # 40 ms frames
    hop = frame // 2
    min_lag = int(sample_rate / max_hz)
    max_lag = int(sample_rate / min_hz)
    f0s: list[float] = []
    for start in range(0, max(0, len(x) - frame), hop):
        seg = x[start:start + frame]
        if float(np.sqrt(np.mean(seg ** 2))) < 0.01:  # silence / near-silence
            continue
        seg = seg - seg.mean()
        corr = np.correlate(seg, seg, mode="full")[len(seg) - 1:]
        if corr[0] <= 0:
            continue
        window = corr[min_lag:max_lag]
        if window.size == 0:
            continue
        lag = int(np.argmax(window)) + min_lag
        if corr[lag] / corr[0] > 0.3:  # periodicity threshold
            f0s.append(sample_rate / lag)
    if not f0s:
        return None
    f0s.sort()
    return f0s[len(f0s) // 2]
