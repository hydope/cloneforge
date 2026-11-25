"""Backend registry: every adapter CloneForge can route to.

Design rules:
- Adapters are *lazy*: importing this module never imports torch or any
  backend. Detection is a cheap import-spec / binary probe.
- Licence is recorded for code and weights *separately*, because several
  famous repos are MIT code over non-commercial weights (F5-TTS, XTTS-v2).
- Benchmark figures are the backends' own published numbers, each with its
  benchmark name attached. A figure without a benchmark is not stored.
"""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Backend:
    id: str
    name: str
    repo: str
    stars: int | None  # GitHub stars at research time (Nov 2026); None = not a repo product
    kind: str  # "neural-clone" | "tts-only" | "voice-conversion" | "dsp-baseline" | "reference-gen"
    min_sample_s: float  # shortest reference the backend can use at all
    ideal_sample_s: float  # reference length the vendor/paper recommends
    languages: tuple[str, ...]  # ISO codes it *claims*; () = unknown
    licence_code: str
    licence_weights: str
    commercial_ok: bool  # True only if BOTH code and weights allow commercial use
    vram_gb: float | None  # None = CPU-runnable / not applicable
    strengths: dict[str, int] = field(default_factory=dict)  # dimension -> 0..5, evidence-based
    sim_en: float | None = None  # published speaker-similarity on the named benchmark
    sim_benchmark: str = ""
    wer_en: float | None = None  # published word-error-rate (%) on the named benchmark
    wer_benchmark: str = ""
    probe_module: str = ""  # python module whose presence means "installed"
    probe_binary: str = ""  # executable whose presence means "installed"
    install_hint: str = ""
    notes: str = ""

    def installed(self) -> bool:
        return self.status()[0]

    def status(self) -> tuple[bool, str]:
        """(installed, via) — probed the same way the bench runs the backend.

        Most backends are probed in the current environment. The coqui-tts
        backends (YourTTS, XTTS-v2) usually live in the side venv
        (.venv-yourtts) and are executed by subprocess — probing only the
        current environment made `doctor` report them "not installed"
        while the bench ran them (v0.2 bug, critic-found). They are now
        probed through cloneforge.neural.tts_interpreter(), the exact
        probe the runners use, so doctor and bench cannot disagree.
        """
        if self.id in _SIDE_VENV_IDS:
            from .neural import tts_interpreter

            interp = tts_interpreter()
            if interp is not None:
                return True, f"side venv interpreter {interp}"
            return False, ""
        if self.id == "voxcpm2":
            from .voxcpm import voxcpm_interpreter

            interp = voxcpm_interpreter()
            if interp is not None:
                return True, f"side venv interpreter {interp}"
            return False, ""
        if self.id == "dotstts":
            from .dotstts import dotstts_interpreter

            if dotstts_interpreter() is not None:
                return True, "dots.tts interpreter probed"
            return False, ""
        if self.probe_module and importlib.util.find_spec(self.probe_module) is not None:
            return True, "current environment"
        if self.probe_binary and shutil.which(self.probe_binary) is not None:
            return True, f"binary {self.probe_binary}"
        if self.id in _BUILTIN_IDS:
            return True, "built into CloneForge"
        return False, ""


# Strength scale: 5 = best published evidence in class, 1 = documented weakness.
# Only dimensions with actual published evidence get a score.
BACKENDS: tuple[Backend, ...] = (
    Backend(
        id="dotstts",
        name="dots.tts (SOAR)",
        repo="studio-dots-ai/dots.tts",
        stars=1435,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=10.0,
        languages=("en", "zh"),
        licence_code="Apache-2.0",
        licence_weights="Apache-2.0",
        commercial_ok=True,
        vram_gb=10.51,
        strengths={"similarity": 5, "pronunciation": 4},
        sim_en=0.792,
        sim_benchmark="Seed-TTS-Eval avg (WavLM SIM, tech report)",
        wer_en=2.95,
        wer_benchmark="Seed-TTS-Eval avg WER % (tech report)",
        probe_module="dots_tts",
        install_hint="See https://github.com/studio-dots-ai/dots.tts — research-grade, heavy GPU.",
        notes="Highest published SIM of any open model; very new, tooling is research-grade.",
    ),
    Backend(
        id="voxcpm2",
        name="VoxCPM2",
        repo="OpenBMB/VoxCPM",
        stars=42922,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=10.0,
        languages=("en", "zh"),
        licence_code="Apache-2.0",
        licence_weights="Apache-2.0",
        commercial_ok=True,
        vram_gb=8.0,
        strengths={"similarity": 4, "pronunciation": 4},
        sim_en=0.753,
        sim_benchmark="Seed-TTS-Eval test-en (WavLM SIM, repo tables)",
        wer_en=1.84,
        wer_benchmark="Seed-TTS-Eval test-en WER % (repo tables)",
        probe_module="voxcpm",
        install_hint="pip install voxcpm  (see https://github.com/OpenBMB/VoxCPM)",
        notes="Most established fully-Apache open cloner; ~8 GB VRAM.",
    ),
    Backend(
        id="fishs2",
        name="Fish Speech S2",
        repo="fishaudio/fish-speech",
        stars=33845,
        kind="neural-clone",
        min_sample_s=10.0,
        ideal_sample_s=30.0,
        languages=("en", "zh", "ja"),
        licence_code="Fish Audio Research Licence",
        licence_weights="Research-only (S2 Pro)",
        commercial_ok=False,
        vram_gb=12.0,
        strengths={"pronunciation": 5, "emotion": 4},
        wer_en=0.99,
        wer_benchmark="Seed-TTS-Eval test-en WER % (vendor tech report)",
        probe_module="fish_speech",
        install_hint="See https://github.com/fishaudio/fish-speech",
        notes="Best published English WER; weights are research-only — not commercial.",
    ),
    Backend(
        id="cosyvoice3",
        name="CosyVoice 3",
        repo="QwenAudio/CosyVoice",
        stars=24492,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=10.0,
        languages=("en", "zh", "ja", "ko"),
        licence_code="Apache-2.0",
        licence_weights="Apache-2.0",
        commercial_ok=True,
        vram_gb=8.0,
        strengths={"similarity": 3, "pronunciation": 4},
        sim_en=0.718,
        sim_benchmark="Seed-TTS-Eval test-en (WavLM SIM)",
        wer_en=2.02,
        wer_benchmark="Seed-TTS-Eval test-en WER %",
        probe_module="cosyvoice",
        install_hint="See https://github.com/QwenAudio/CosyVoice",
        notes="Narrow language list (9); robust under noisy references in RVCBench.",
    ),
    Backend(
        id="f5tts",
        name="F5-TTS",
        repo="SWivid/F5-TTS",
        stars=15644,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=12.0,
        languages=("en", "zh"),
        licence_code="MIT",
        licence_weights="CC-BY-NC (non-commercial!)",
        commercial_ok=False,
        vram_gb=6.0,
        strengths={"similarity": 3},
        sim_en=0.670,
        sim_benchmark="Seed-TTS-Eval test-en (WavLM SIM, paper tables)",
        wer_en=2.00,
        wer_benchmark="Seed-TTS-Eval test-en WER % (paper tables)",
        probe_module="f5_tts",
        install_hint="pip install f5-tts  (see https://github.com/SWivid/F5-TTS)",
        notes="Code is MIT but weights are CC-BY-NC — commercial use is NOT allowed.",
    ),
    Backend(
        id="higgs2",
        name="Higgs Audio V2",
        repo="boson-ai/higgs-audio",
        stars=8390,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=10.0,
        languages=("en",),
        licence_code="Non-commercial (successor licences)",
        licence_weights="Non-commercial",
        commercial_ok=False,
        vram_gb=8.0,
        strengths={"emotion": 5},
        sim_en=0.677,
        sim_benchmark="Seed-TTS-Eval test-en (WavLM SIM)",
        wer_en=2.44,
        wer_benchmark="Seed-TTS-Eval test-en WER %",
        probe_module="higgs_audio",
        install_hint="See https://github.com/boson-ai/higgs-audio",
        notes="Best open emotion evidence (EmergentTTS Emotions win-rate 75.7%).",
    ),
    Backend(
        id="xtts2",
        name="XTTS-v2 (idiap fork)",
        repo="idiap/coqui-ai-TTS",
        stars=46272,  # stars belong to the original coqui-ai/TTS repo
        kind="neural-clone",
        min_sample_s=6.0,
        ideal_sample_s=30.0,
        languages=("en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl",
                   "cs", "ar", "zh", "ja", "hu", "ko", "hi"),
        licence_code="MPL-2.0",
        licence_weights="Coqui Public Model Licence (non-commercial!)",
        commercial_ok=False,
        vram_gb=4.0,
        strengths={"similarity": 2},
        sim_en=0.45,
        sim_benchmark="RVCBench (ECAPA SIM — not comparable to WavLM figures)",
        probe_module="TTS",
        install_hint="pip install -e . from https://github.com/idiap/coqui-ai-TTS "
                     "(the original coqui-ai repo is dormant; Coqui Inc. shut down Jan 2024)",
        notes="17 languages — widest open coverage — but lowest top-tier SIM and "
              "non-commercial weights.",
    ),
    Backend(
        id="yourtts",
        name="YourTTS (via coqui/idiap TTS)",
        repo="idiap/coqui-ai-TTS",
        stars=None,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=20.0,
        languages=("en", "fr", "pt"),
        licence_code="MPL-2.0",
        licence_weights="MIT (YourTTS model)",
        commercial_ok=True,
        vram_gb=0.0,
        strengths={"short-sample": 4},
        probe_module="TTS",
        install_hint="Python 3.12: pip install 'coqui-tts[codec]' six "
                     "(the original TTS 0.22 requires Python <3.12 and will "
                     "not install). CPU-runnable; works on very short "
                     "references where XTTS-v2 fails to latch on.",
        notes="The short-sample specialist: designed for few-second references, "
              "runs on CPU. Runner VERIFIED in CloneForge via the coqui-tts "
              "fork in a side venv (.venv-yourtts) — see cloneforge/neural.py.",
    ),
    Backend(
        id="openvoice2",
        name="OpenVoice v2",
        repo="myshell-ai/OpenVoice",
        stars=38314,
        kind="neural-clone",
        min_sample_s=3.0,
        ideal_sample_s=10.0,
        languages=("en", "es", "fr", "zh", "ja", "ko"),
        licence_code="MIT",
        licence_weights="MIT",
        commercial_ok=True,
        vram_gb=4.0,
        strengths={"similarity": 1},
        sim_en=0.24,
        sim_benchmark="RVCBench (ECAPA SIM — lowest of the named models)",
        probe_module="openvoice",
        install_hint="See https://github.com/myshell-ai/OpenVoice",
        notes="Genuinely free for commercial use, but fidelity evidence is no longer competitive.",
    ),
    Backend(
        id="gpt-sovits",
        name="GPT-SoVITS (few-shot)",
        repo="RVC-Boss/GPT-SoVITS",
        stars=None,  # was listed ~65k in Oct-Nov 2026 indexes; live repo status unverified
        kind="neural-clone",
        min_sample_s=5.0,
        ideal_sample_s=60.0,
        languages=("en", "zh", "ja", "ko"),
        licence_code="MIT",
        licence_weights="MIT",
        commercial_ok=True,
        vram_gb=6.0,
        strengths={"short-sample": 3, "similarity": 3},
        probe_module="GPT_SoVITS",
        install_hint="See https://github.com/RVC-Boss/GPT-SoVITS (verify the repo first: "
                     "in Nov 2026 the live repo did not match its indexed star count)",
        notes="Few-shot fine-tune from ~1 minute of audio; zero-shot from ~5 s.",
    ),
    Backend(
        id="rvc",
        name="RVC (Retrieval-based Voice Conversion)",
        repo="RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
        stars=39274,
        kind="voice-conversion",
        min_sample_s=60.0,
        ideal_sample_s=600.0,
        languages=(),  # language-agnostic: it converts a performance, it does not read text
        licence_code="MIT",
        licence_weights="MIT (train your own model)",
        commercial_ok=True,
        vram_gb=6.0,
        strengths={"pace": 5, "emotion": 5},
        probe_module="infer",
        install_hint="See https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
        notes="Speech-to-speech: preserves the source performance's timing, hesitations "
              "and emotion by construction. Needs a trained per-voice model. "
              "CloneForge ships the interface; conversion itself runs in RVC.",
    ),
    Backend(
        id="piper",
        name="Piper (reference & base TTS)",
        repo="rhasspy/piper",
        stars=None,
        kind="reference-gen",
        min_sample_s=0.0,
        ideal_sample_s=0.0,
        languages=("en",),
        licence_code="MIT",
        licence_weights="Varies per voice (check each voice's card)",
        commercial_ok=True,
        vram_gb=0.0,
        probe_module="piper",
        install_hint="pip install piper-tts, then download a voice .onnx from "
                     "https://huggingface.co/rhasspy/piper-voices",
        notes="Not a cloner. CloneForge uses Piper to *generate synthetic reference "
              "speakers* for testing, and as the base voice for the DSP baseline.",
    ),
    Backend(
        id="dsp-prosody",
        name="DSP ProsodyMatch — CONTROL, not a voice clone (prosody-matched baseline)",
        repo="",
        stars=None,
        kind="dsp-baseline",
        min_sample_s=2.0,
        ideal_sample_s=10.0,
        languages=("en",),
        licence_code="MIT (this project)",
        licence_weights="n/a (no neural weights)",
        commercial_ok=True,
        vram_gb=0.0,
        strengths={"pace": 3},
        notes="Built into CloneForge, always available. Measures the reference's median "
              "pitch (F0) and speaking rate, renders the text with Piper, then pitch/tempo-"
              "shifts the result toward the reference with ffmpeg. It is a *baseline*, not "
              "neural cloning: expect measurable pace/pitch matching and LOW speaker "
              "similarity — the bench harness will show you the real numbers.",
    ),
)

_BUILTIN_IDS = frozenset({"dsp-prosody"})

# Backends executed via the coqui-tts side venv (.venv-yourtts) subprocess.
_SIDE_VENV_IDS = frozenset({"xtts2", "yourtts"})

BY_ID: dict[str, Backend] = {b.id: b for b in BACKENDS}


def get(backend_id: str) -> Backend:
    return BY_ID[backend_id]


def installed_backends() -> list[Backend]:
    return [b for b in BACKENDS if b.installed()]


def clone_capable() -> list[Backend]:
    return [b for b in BACKENDS if b.kind in ("neural-clone", "dsp-baseline", "voice-conversion")]
