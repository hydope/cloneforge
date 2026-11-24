"""Evidence-based routing.

Given a job (language, reference length, priority, commercial use), rank the
registered backends and explain each ranking with the published evidence
behind it. The router never recommends a backend for a language it does not
claim, never recommends non-commercial weights for a commercial job, and
flags languages with no published cloning accuracy — Urdu first among them —
as UNVERIFIED instead of pretending a ranking is evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .backends import BACKENDS, Backend

PRIORITIES = ("accuracy", "emotion", "speed", "short-sample", "pace")

# Languages for which *no* top backend publishes cloning SIM/WER/prosody
# evidence (verified in the Nov 2026 research). Coverage claims are not
# accuracy evidence.
UNVERIFIED_LANGUAGES = {
    "ur": "Urdu: no top-10 tool publishes Urdu cloning SIM, WER or prosody "
          "figures. Urdu is absent from the standard 24-language cloning "
          "test set (Hindi is in it; Urdu is not). Any pick below is a "
          "coverage claim only — run the CloneForge listening test "
          "(cloneforge bench) on the real speaker before trusting it.",
}

_PRIORITY_DIMENSION = {
    "accuracy": "similarity",
    "emotion": "emotion",
    "short-sample": "short-sample",
    "pace": "pace",
}


@dataclass
class Recommendation:
    backend: Backend
    score: float
    reasons: list[str]
    warnings: list[str]


def route(
    language: str = "en",
    sample_seconds: float = 10.0,
    priority: str = "accuracy",
    commercial: bool = False,
    installed_only: bool = False,
) -> tuple[list[Recommendation], list[str]]:
    """Return (ranked recommendations, job-level warnings)."""
    if priority not in PRIORITIES:
        raise ValueError(f"priority must be one of {PRIORITIES}")
    warnings: list[str] = []
    lang = language.lower()
    if lang in UNVERIFIED_LANGUAGES:
        warnings.append("UNVERIFIED LANGUAGE — " + UNVERIFIED_LANGUAGES[lang])
    if priority == "pace":
        warnings.append(
            "PACE: text-to-speech backends invent new timing — none publishes "
            "a pace/duration error. Only speech-to-speech conversion (RVC) "
            "preserves a real performance's pace. TTS picks below are ranked "
            "on similarity evidence, not pace fidelity."
        )

    recs: list[Recommendation] = []
    for b in BACKENDS:
        if b.kind in ("reference-gen",):
            continue
        reasons: list[str] = []
        bwarnings: list[str] = []
        score = 0.0

        if installed_only and not b.installed():
            continue
        if commercial and not b.commercial_ok:
            bwarnings.append(
                f"excluded for commercial use: weights licence is {b.licence_weights}")
            continue
        if sample_seconds < b.min_sample_s:
            bwarnings.append(
                f"needs >= {b.min_sample_s:.0f}s of reference; you have "
                f"{sample_seconds:.0f}s — excluded")
            continue
        if sample_seconds < b.ideal_sample_s:
            bwarnings.append(
                f"works with {sample_seconds:.0f}s but its evidence assumes "
                f"~{b.ideal_sample_s:.0f}s references")
            score -= 1.0

        if b.kind == "voice-conversion":
            if priority == "pace":
                score += 10.0
                reasons.append("speech-to-speech: preserves the performed pace, "
                               "hesitations and emotion by construction")
            else:
                score -= 5.0
                reasons.append("voice conversion, not TTS: it converts a performed "
                               "take, it does not read text")
        if b.kind == "dsp-baseline":
            score -= 2.0
            reasons.append("built-in DSP baseline: measurable pace/pitch matching, "
                           "low speaker similarity — included so the bench always "
                           "has one runnable backend")

        dim = _PRIORITY_DIMENSION.get(priority)
        if dim and dim in b.strengths:
            score += b.strengths[dim] * 2.0
            reasons.append(f"{dim} strength {b.strengths[dim]}/5 (published evidence)")
        if priority == "speed" and b.vram_gb == 0.0:
            score += 6.0
            reasons.append("CPU-runnable: no GPU needed")
        if b.sim_en is not None and priority == "accuracy":
            score += b.sim_en * 5.0
            reasons.append(f"published SIM {b.sim_en:.3f} — {b.sim_benchmark}")
        if b.wer_en is not None and priority == "accuracy":
            score += max(0.0, (3.0 - b.wer_en))  # lower WER is better
            reasons.append(f"published WER {b.wer_en:.2f}% — {b.wer_benchmark}")
        if lang in b.languages:
            score += 2.0
            reasons.append(f"claims {lang} support")
        elif b.languages:
            bwarnings.append(f"does not claim {lang}; cross-lingual use is unproven for it")
            score -= 3.0
        if b.commercial_ok:
            reasons.append(f"licence clear (code {b.licence_code}, weights {b.licence_weights})")
        else:
            bwarnings.append(f"weights licence: {b.licence_weights} — non-commercial")

        recs.append(Recommendation(backend=b, score=score, reasons=reasons,
                                   warnings=bwarnings))

    recs.sort(key=lambda r: r.score, reverse=True)
    return recs, warnings
