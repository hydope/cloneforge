"""The benchmark harness — CloneForge's core product.

Runs the SAME line through every runnable backend against the SAME
reference, then measures what can honestly be measured:

- pace: speaking-rate difference vs the reference (measured from WAV
  durations and the known word count — exact),
- pitch: median F0 of output vs reference (autocorrelation — measured),
- pronunciation: WER of a local ASR transcript vs the target line
  (measured ONLY if a local ASR is installed; otherwise NOT MEASURED),
- speaker similarity: embedding cosine (measured ONLY if a local speaker
  embedder is installed; otherwise NOT MEASURED).

Rows are categorised and reported separately:

- CLONE — a real voice-cloning backend (neural zero/few-shot);
- CONTROL — NOT a voice clone: the DSP prosody-matched baseline and the
  plain Piper base voice. Controls exist to calibrate the metrics (a
  control's similarity shows what "a different speaker" scores); they
  must never be read as clones, however good their pace numbers look.

No metric is ever estimated. A backend that is not installed, or whose
runner is not implemented, is reported as NOT RUN — never scored.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import audio
from .backends import BACKENDS, BY_ID
from .metrics import media_duration_seconds, median_f0_hz, rate_difference_pct, speech_rate_wpm, wer

NOT_MEASURED = "NOT MEASURED"
NOT_RUN = "NOT RUN"

CLONE = "CLONE"
CONTROL = "CONTROL"


def category_for(backend_id: str) -> str:
    """CLONE or CONTROL for a backend id — the separation is structural."""
    kind = BY_ID[backend_id].kind
    return CONTROL if kind in ("dsp-baseline", "reference-gen") else CLONE


@dataclass
class BenchRow:
    backend_id: str
    backend_name: str
    status: str  # "ok" | NOT_RUN
    category: str = CLONE  # CLONE | CONTROL
    note: str = ""
    output_path: str = ""
    duration_s: float | None = None
    rate_wpm: float | None = None
    rate_diff_pct: float | None = None
    f0_hz: float | None = None
    f0_diff_pct: float | None = None
    wer_pct: float | str = NOT_MEASURED
    similarity: float | str = NOT_MEASURED  # GE2E (resemblyzer) cosine
    similarity_ecapa: float | str = NOT_MEASURED  # ECAPA-TDNN cosine — separate scorer
    latency_s: float | None = None  # wall-clock seconds for the run, measured


@dataclass
class BenchReport:
    line: str
    reference_path: str
    reference_duration_s: float
    reference_rate_wpm: float
    reference_f0_hz: float | None
    rows: list[BenchRow] = field(default_factory=list)
    asr_status: str = NOT_MEASURED
    embedder_status: str = NOT_MEASURED
    embedder_status_ecapa: str = NOT_MEASURED
    control_self_similarity: float | str = NOT_MEASURED
    control_different_speaker_similarity: float | str = NOT_MEASURED
    control_self_similarity_ecapa: float | str = NOT_MEASURED
    control_different_speaker_similarity_ecapa: float | str = NOT_MEASURED


def _try_asr():
    """Return a transcribe(path)->str callable, or None."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def transcribe(path: str) -> str:
        segments, _info = model.transcribe(path)
        return " ".join(s.text for s in segments).strip()

    return transcribe


def runner_availability() -> dict[str, tuple[bool, str]]:
    """backend id -> (can execute here, reason) for every bench runner.

    This is the single registry doctor and the bench both consult: if a
    runner can execute, doctor must report the backend INSTALLED, and
    vice versa (regression-tested — the v0.2 doctor bug was the two
    disagreeing).

    $CLONEFORGE_DISABLE_BACKENDS (comma-separated ids) is an operator
    kill-switch: a disabled backend reports NOT RUN with the reason
    stated, and doctor's status() applies the same switch, so the two
    still cannot disagree.
    """
    import importlib.util
    import os

    from .dotstts import dotstts_available
    from .neural import xtts_available, yourtts_available
    from .voxcpm import voxcpm_available

    disabled = {s.strip() for s in
                os.environ.get("CLONEFORGE_DISABLE_BACKENDS", "").split(",")
                if s.strip()}

    disabled_reason = "disabled by operator via CLONEFORGE_DISABLE_BACKENDS"

    def probe(bid, fn):
        if bid in disabled:
            return (False, disabled_reason)
        return fn()

    return {
        "dsp-prosody": probe("dsp-prosody", lambda: (True, "built into CloneForge")),
        "piper": probe("piper", lambda: (
            importlib.util.find_spec("piper") is not None,
            "piper-tts in current environment")),
        "yourtts": probe("yourtts", yourtts_available),
        "xtts2": probe("xtts2", xtts_available),
        "voxcpm2": probe("voxcpm2", voxcpm_available),
        "dotstts": probe("dotstts", dotstts_available),
    }


def executable_runner_ids() -> list[str]:
    return [bid for bid, (ok, _why) in runner_availability().items() if ok]


def _make_runner(backend_id: str, line: str, reference_wav, reference_text: str):
    from .dotstts import dotstts_clone
    from .neural import xtts_clone, yourtts_clone
    from .voxcpm import voxcpm_clone

    runners = {
        "dsp-prosody": lambda p: audio.dsp_clone(
            line, reference_wav, p, reference_text=reference_text),
        "piper": lambda p: {"output_path": str(audio.piper_synthesize(line, p))},
        "yourtts": lambda p: yourtts_clone(line, reference_wav, p),
        "xtts2": lambda p: xtts_clone(line, reference_wav, p),
        "voxcpm2": lambda p: voxcpm_clone(line, reference_wav, p,
                                          reference_text=reference_text),
        "dotstts": lambda p: dotstts_clone(line, reference_wav, p),
    }
    return runners[backend_id]


def run_bench(line: str, reference_wav: str | Path,
              out_dir: str | Path,
              reference_text: str | None = None) -> BenchReport:
    """Benchmark every runnable backend on `line` against `reference_wav`.

    The reference must be a recording (real or synthetic) of the SAME line;
    its transcript is `line` itself (pass reference_text only if the
    reference speaks different words than the target line).
    """
    import time

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ref_text = reference_text if reference_text is not None else line
    ref_dur = media_duration_seconds(reference_wav)
    words = max(1, len(line.split()))
    ref_rate = speech_rate_wpm(words, ref_dur)
    ref_samples, ref_sr = audio.read_wav_samples(reference_wav)
    ref_f0 = median_f0_hz(ref_samples, ref_sr)

    transcribe = _try_asr()

    from .similarity import get_ecapa_embedder, get_embedder

    embedder = get_embedder()
    ecapa = get_ecapa_embedder()

    report = BenchReport(
        line=line,
        reference_path=str(reference_wav),
        reference_duration_s=ref_dur,
        reference_rate_wpm=ref_rate,
        reference_f0_hz=ref_f0,
        asr_status="faster-whisper (tiny, local)" if transcribe else NOT_MEASURED,
        embedder_status=embedder.method if embedder else NOT_MEASURED,
        embedder_status_ecapa=ecapa.method if ecapa else NOT_MEASURED,
    )

    availability = runner_availability()

    for b in BACKENDS:
        if b.id in availability:
            can_run, why = availability[b.id]
            if not can_run:
                report.rows.append(BenchRow(
                    b.id, b.name, NOT_RUN, category=category_for(b.id),
                    note=f"runner present but backend unavailable: {why}"))
                continue
            out_path = out / f"{b.id}.wav"
            runner = _make_runner(b.id, line, reference_wav, ref_text)
            start = time.perf_counter()
            try:
                runner(out_path)
            except Exception as exc:  # noqa: BLE001 — a failed run is data, not a crash
                report.rows.append(BenchRow(
                    b.id, b.name, NOT_RUN, category=category_for(b.id),
                    latency_s=round(time.perf_counter() - start, 2),
                    note=f"runner failed: {exc}"))
                continue
            latency = round(time.perf_counter() - start, 2)
            row = _score(b.id, b.name, out_path, line, ref_rate, ref_f0, transcribe)
            row.latency_s = latency
            report.rows.append(row)
        elif b.kind == "voice-conversion":
            report.rows.append(BenchRow(
                b.id, b.name, NOT_RUN, category=category_for(b.id),
                note="interface-only: conversion runs in RVC itself; "
                     "CloneForge does not wrap it yet"))
        elif b.kind in ("neural-clone",):
            state = "installed" if b.installed() else "not installed"
            report.rows.append(BenchRow(
                b.id, b.name, NOT_RUN, category=category_for(b.id),
                note=f"adapter registered, backend {state}; runner is "
                     "interface-only (see docs/BACKENDS.md)"))

    _apply_similarity(report, embedder, reference_wav, scorer="ge2e")
    _apply_similarity(report, ecapa, reference_wav, scorer="ecapa")

    # Order: measured CLONEs first (similarity-first, the metric cloning is
    # for), then CONTROLs, then NOT RUN rows. Categories never interleave.
    def sort_key(r: BenchRow):
        cat_rank = {CLONE: 0, CONTROL: 1}.get(r.category, 2) if r.status == "ok" else 3
        sim = r.similarity if isinstance(r.similarity, float) else (
            r.similarity_ecapa if isinstance(r.similarity_ecapa, float) else -2.0)
        return (cat_rank, -sim,
                abs(r.rate_diff_pct) if r.rate_diff_pct is not None else 1e9)

    report.rows.sort(key=sort_key)
    return report


def _apply_similarity(report: BenchReport, embedder, reference_wav,
                      scorer: str = "ge2e") -> None:
    """Batch-embed reference + every ok output with ONE scorer.

    GE2E and ECAPA are applied by separate calls and stored in separate
    fields — the two scorers' numbers are never blended or averaged.
    """
    if embedder is None:
        return
    ok_rows = [r for r in report.rows if r.status == "ok" and r.output_path]
    if not ok_rows:
        return
    from .metrics import cosine_similarity

    field_name = "similarity" if scorer == "ge2e" else "similarity_ecapa"
    paths = [str(reference_wav)] + [r.output_path for r in ok_rows]
    try:
        embeddings = embedder.embed_many(paths)
    except Exception:  # noqa: BLE001 — embedder failure means NOT MEASURED
        if scorer == "ge2e":
            report.embedder_status = NOT_MEASURED
        else:
            report.embedder_status_ecapa = NOT_MEASURED
        return
    ref_emb, out_embs = embeddings[0], embeddings[1:]
    for row, emb in zip(ok_rows, out_embs, strict=True):
        try:
            setattr(row, field_name, round(cosine_similarity(ref_emb, emb), 4))
        except Exception:  # noqa: BLE001
            setattr(row, field_name, NOT_MEASURED)
    # Sanity controls: reference vs itself must be ~1.0; a CONTROL output
    # (a different speaker by construction) is the different-speaker control.
    self_sim = round(cosine_similarity(ref_emb, ref_emb), 4)
    diff_sim: float | str = NOT_MEASURED
    for row, emb in zip(ok_rows, out_embs, strict=True):
        if row.category == CONTROL:
            diff_sim = round(cosine_similarity(ref_emb, emb), 4)
            break
    if scorer == "ge2e":
        report.control_self_similarity = self_sim
        report.control_different_speaker_similarity = diff_sim
    else:
        report.control_self_similarity_ecapa = self_sim
        report.control_different_speaker_similarity_ecapa = diff_sim


def _score(backend_id, name, out_path, line, ref_rate, ref_f0, transcribe) -> BenchRow:
    dur = media_duration_seconds(out_path)
    words = max(1, len(line.split()))
    rate = speech_rate_wpm(words, dur)
    samples, sr = audio.read_wav_samples(out_path)
    f0 = median_f0_hz(samples, sr)
    row = BenchRow(
        backend_id=backend_id, backend_name=name, status="ok",
        category=category_for(backend_id),
        output_path=str(out_path), duration_s=dur, rate_wpm=rate,
        rate_diff_pct=rate_difference_pct(ref_rate, rate), f0_hz=f0,
        f0_diff_pct=(rate_difference_pct(ref_f0, f0)
                     if (ref_f0 and f0) else None),
    )
    if transcribe is not None:
        try:
            row.wer_pct = round(wer(line, transcribe(str(out_path))), 2)
        except Exception:  # noqa: BLE001 — ASR failure means NOT MEASURED
            row.wer_pct = NOT_MEASURED
    return row


def _fmt(value, suffix=""):
    return NOT_MEASURED if value is None else f"{value:.2f}{suffix}"


_TABLE_HEADER = (
    "| # | Backend | Status | Duration | Latency | Rate diff (pace) | F0 diff | "
    "WER (pronunciation) | Similarity GE2E | Similarity ECAPA | Note |"
)


def _table(rows: list[BenchRow]) -> list[str]:
    lines = [_TABLE_HEADER, "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, start=1):
        lines.append(
            f"| {i} | {r.backend_name} | {r.status} | {_fmt(r.duration_s, 's')} | "
            f"{_fmt(r.latency_s, 's')} | "
            f"{_fmt(r.rate_diff_pct, '%')} | {_fmt(r.f0_diff_pct, '%')} | "
            f"{r.wer_pct if isinstance(r.wer_pct, str) else _fmt(r.wer_pct, '%')} | "
            f"{r.similarity} | {r.similarity_ecapa} | {r.note} |")
    return lines


def report_markdown(report: BenchReport) -> str:
    ref_line = (
        f"Reference: `{report.reference_path}` — "
        f"{report.reference_duration_s:.2f}s, "
        f"{report.reference_rate_wpm:.1f} wpm, "
        f"F0 {_fmt(report.reference_f0_hz, ' Hz')}"
    )
    asr_line = (f"ASR for WER: {report.asr_status} · "
                f"Speaker embedder GE2E: {report.embedder_status} · "
                f"Speaker embedder ECAPA: {report.embedder_status_ecapa}")
    controls_line = (
        f"Similarity controls (GE2E): reference vs itself = "
        f"{report.control_self_similarity} (must be ~1.0); different speaker "
        f"(CONTROL voice) vs reference = "
        f"{report.control_different_speaker_similarity} (must be clearly "
        "lower than a clone's score)\n"
        f"Similarity controls (ECAPA): reference vs itself = "
        f"{report.control_self_similarity_ecapa} (must be ~1.0); different "
        f"speaker (CONTROL voice) vs reference = "
        f"{report.control_different_speaker_similarity_ecapa} (must be "
        "clearly lower than a clone's score)")
    clones = [r for r in report.rows if r.status == "ok" and r.category == CLONE]
    controls = [r for r in report.rows if r.status == "ok" and r.category == CONTROL]
    not_run = [r for r in report.rows if r.status != "ok"]
    lines = [
        "# CloneForge bench report",
        "",
        f"Line: “{report.line}”",
        ref_line,
        asr_line,
        controls_line,
        "",
        "## Voice clones (neural)",
        "",
        *_table(clones),
        "",
        "## CONTROLS — not voice clones",
        "",
        ("The rows below are **controls, not voice clones**: a prosody-matched "
         "DSP baseline and a plain TTS voice. They calibrate the metrics — "
         "their similarity scores show what a *different speaker* measures — "
         "and a good pace number here does NOT mean a good clone."),
        "",
        *_table(controls),
        "",
        "## Not run",
        "",
        *_table(not_run),
    ]
    how = (
        "How each metric was measured: pace = speaking-rate difference from "
        "exact WAV durations and the known word count; F0 = median "
        "autocorrelation pitch; WER = local ASR transcript vs the target line "
        f"({report.asr_status}); latency = wall-clock seconds for the "
        "backend run (measured, includes model load when the runner loads "
        "per call); similarity GE2E = local speaker-embedding cosine "
        f"({report.embedder_status}); similarity ECAPA = local "
        "speaker-embedding cosine "
        f"({report.embedder_status_ecapa}). GE2E and ECAPA are DIFFERENT "
        "scorers on different scales — the two columns are reported "
        "separately and are never blended or compared against each other. "
        "Anything not measured says so — CloneForge never estimates a "
        "quality number."
    )
    lines += ["", how]
    return "\n".join(lines) + "\n"


def report_html(report: BenchReport) -> str:
    md = report_markdown(report)
    body = html.escape(md).replace("\n", "<br>\n")
    return ("<!doctype html><meta charset=utf-8>"
            "<title>CloneForge bench report</title>"
            f"<body style='font-family:system-ui;max-width:60rem;margin:2rem auto'>"
            f"<pre style='white-space:pre-wrap'>{body}</pre></body>\n")


def save_report(report: BenchReport, out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    paths = {
        "markdown": str(out / "bench-report.md"),
        "html": str(out / "bench-report.html"),
        "json": str(out / "bench-report.json"),
    }
    Path(paths["markdown"]).write_text(report_markdown(report), encoding="utf-8")
    Path(paths["html"]).write_text(report_html(report), encoding="utf-8")
    Path(paths["json"]).write_text(
        json.dumps(report, default=lambda o: o.__dict__, indent=2), encoding="utf-8")
    return paths
