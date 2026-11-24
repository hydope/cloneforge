"""Audio helpers and the two backends that genuinely run on a CPU-only box:

1. Piper — neural TTS used to *generate synthetic reference speakers* and as
   the base voice for the DSP baseline. Piper is not a cloner and is never
   described as one.
2. DSP ProsodyMatch — CloneForge's built-in baseline: measure the reference's
   median F0 and speaking rate, render with Piper, then pitch/tempo-shift
   toward the reference with ffmpeg. Every step is measurable, and the bench
   harness reports what it actually achieved.
"""

from __future__ import annotations

import subprocess
import wave
from contextlib import closing
from pathlib import Path

from .metrics import median_f0_hz, speech_rate_wpm, wav_duration_seconds

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def read_wav_samples(path: str | Path) -> tuple[list[float], int]:
    """Read a 16-bit PCM WAV into float samples in [-1, 1] (mono-mixed)."""
    with closing(wave.open(str(path), "rb")) as w:
        rate = w.getframerate()
        channels = w.getnchannels()
        width = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError(f"expected 16-bit PCM WAV, got sample width {width}")
    import numpy as np

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data.tolist(), rate


def piper_model(name: str = "en_US-amy-medium") -> Path:
    model = MODELS_DIR / f"{name}.onnx"
    if not model.exists():
        raise FileNotFoundError(
            f"Piper voice not found: {model}. Download a voice .onnx + .onnx.json "
            "from https://huggingface.co/rhasspy/piper-voices into models/ "
            "(see docs/INSTALL.md).")
    return model


def piper_synthesize(text: str, out_wav: str | Path,
                     model_name: str = "en_US-amy-medium") -> Path:
    """Render text with Piper (neural TTS). Returns the output path."""
    from piper import PiperVoice

    model = piper_model(model_name)
    voice = PiperVoice.load(str(model))
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    with closing(wave.open(str(out), "wb")) as wav_file:
        voice.synthesize_wav(text, wav_file)
    return out


def make_reference(text: str, out_wav: str | Path,
                   model_name: str = "en_US-lessac-medium") -> Path:
    """Generate a *synthetic* reference speaker clip for testing.

    CloneForge ships no real person's voice. Test fixtures are synthesized
    so anyone can run the full pipeline without recording anyone.
    """
    return piper_synthesize(text, out_wav, model_name=model_name)


def dsp_clone(text: str, reference_wav: str | Path, out_wav: str | Path,
              base_model: str = "en_US-amy-medium",
              reference_text: str | None = None) -> dict:
    """The DSP ProsodyMatch baseline. Returns a measurement dict.

    Steps (all measured, all reported):
    1. median F0 + duration of the reference,
    2. render `text` with the Piper base voice,
    3. ffmpeg rubberband pitch-shift toward the reference F0 ratio and —
       only when the reference transcript is known (bench mode passes it,
       or a sidecar <reference>.txt exists) — atempo toward the reference's
       seconds-per-word pace. Without a transcript, pace matching is
       reported as NOT MEASURED / NOT APPLIED rather than guessed.
    """
    if reference_text is None:
        sidecar = Path(str(reference_wav) + ".txt")
        if sidecar.exists():
            reference_text = sidecar.read_text(encoding="utf-8")
    ref_samples, ref_rate = read_wav_samples(reference_wav)
    ref_f0 = median_f0_hz(ref_samples, ref_rate)
    ref_dur = wav_duration_seconds(reference_wav)

    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_out = out.with_suffix(".raw.wav")
    piper_synthesize(text, raw_out, model_name=base_model)

    base_samples, base_rate = read_wav_samples(raw_out)
    base_f0 = median_f0_hz(base_samples, base_rate)
    base_dur = wav_duration_seconds(raw_out)

    filters: list[str] = []
    pitch_ratio = None
    if ref_f0 and base_f0:
        pitch_ratio = ref_f0 / base_f0
        filters.append(f"rubberband=pitch={pitch_ratio:.4f}")
    # Pace: match seconds-per-word of the reference — only with a transcript.
    ref_words = len(reference_text.split()) if reference_text else 0
    text_words = max(1, len(text.split()))
    tempo = None
    if ref_words > 0:
        target_dur = ref_dur / ref_words * text_words
        tempo = base_dur / target_dur if target_dur > 0 else 1.0
        tempo = min(2.0, max(0.5, tempo))  # ffmpeg atempo single-stage range
        if abs(tempo - 1.0) > 0.01:
            filters.append(f"atempo={tempo:.4f}")

    if filters:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(raw_out),
             "-af", ",".join(filters), str(out)],
            check=True)
    else:
        raw_out.replace(out)
    if raw_out.exists() and raw_out != out:
        raw_out.unlink()

    final_dur = wav_duration_seconds(out)
    return {
        "backend": "dsp-prosody",
        "reference_f0_hz": ref_f0,
        "base_f0_hz": base_f0,
        "pitch_ratio_applied": pitch_ratio,
        "tempo_applied": tempo,
        "reference_duration_s": ref_dur,
        "base_duration_s": base_dur,
        "output_duration_s": final_dur,
        "reference_rate_wpm": speech_rate_wpm(ref_words, ref_dur) if ref_words else None,
        "output_path": str(out),
    }
