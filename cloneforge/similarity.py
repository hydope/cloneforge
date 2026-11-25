"""Speaker similarity — measured locally, or NOT MEASURED.

The embedder is resemblyzer's VoiceEncoder (GE2E speaker verification,
256-dim embeddings). It is used two ways, in order:

1. in-process, when `resemblyzer` is importable in this interpreter;
2. via a subprocess in an interpreter that can import it — typically the
   coqui-tts side venv (.venv-yourtts), which already carries torch, so
   the embedder does not force a second torch install into the main venv.
   Override the search with $CLONEFORGE_EMBED_PYTHON.

Either way the number produced is the cosine between two embeddings
computed by the same model on this machine. If neither path works, the
caller must report NOT MEASURED — this module never estimates.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .metrics import cosine_similarity

METHOD_INPROCESS = "resemblyzer VoiceEncoder (GE2E, 256-dim), in-process"
METHOD_SUBPROCESS = "resemblyzer VoiceEncoder (GE2E, 256-dim), via {interp}"

_RUNNER = """
import json, sys
from resemblyzer import VoiceEncoder, preprocess_wav
enc = VoiceEncoder()
out = []
for p in sys.argv[1:]:
    out.append(enc.embed_utterance(preprocess_wav(p)).tolist())
print(json.dumps(out))
"""


def _probe(interp: str) -> bool:
    if not Path(interp).exists():
        return False
    proc = subprocess.run(
        [interp, "-c", "import resemblyzer"],
        capture_output=True, timeout=120, check=False)
    return proc.returncode == 0


def embed_interpreter() -> str | None:
    """Interpreter that can import resemblyzer, or None (probed, not guessed)."""
    candidates = []
    env = os.environ.get("CLONEFORGE_EMBED_PYTHON")
    if env:
        candidates.append(env)
    root = Path(__file__).resolve().parent.parent
    candidates.append(str(root / ".venv-yourtts" / "bin" / "python"))
    candidates.append(sys.executable)
    for cand in candidates:
        if cand == sys.executable:
            try:
                import resemblyzer  # noqa: F401

                return cand
            except ImportError:
                continue
        elif _probe(cand):
            return cand
    return None


class Embedder:
    """Batch speaker embedder. `method` names exactly how numbers are made."""

    def __init__(self, mode: str, interp: str | None = None):
        self.mode = mode  # "inprocess" | "subprocess"
        self.interp = interp
        self._encoder = None
        self.method = (
            METHOD_INPROCESS if mode == "inprocess"
            else METHOD_SUBPROCESS.format(interp=interp))

    def embed_many(self, paths: list[str]) -> list[list[float]]:
        if not paths:
            return []
        if self.mode == "inprocess":
            if self._encoder is None:
                from resemblyzer import VoiceEncoder

                self._encoder = VoiceEncoder()
            from resemblyzer import preprocess_wav

            return [self._encoder.embed_utterance(preprocess_wav(p)).tolist()
                    for p in paths]
        proc = subprocess.run(
            [self.interp, "-c", _RUNNER, *paths],
            capture_output=True, text=True, timeout=1200, check=False,
            stdin=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise RuntimeError(
                f"embedder subprocess failed: {proc.stderr.strip()[-500:]}")
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("[")]
        if not lines:
            raise RuntimeError("embedder subprocess produced no embeddings")
        return json.loads(lines[-1])

    def embed(self, path: str) -> list[float]:
        return self.embed_many([path])[0]


def get_embedder() -> Embedder | None:
    """Return a working Embedder, or None when no path is available."""
    try:
        import resemblyzer  # noqa: F401

        return Embedder("inprocess")
    except ImportError:
        pass
    interp = embed_interpreter()
    if interp is not None and interp != sys.executable:
        return Embedder("subprocess", interp)
    return None


def embedder_status() -> tuple[bool, str]:
    emb = get_embedder()
    if emb is None:
        return False, ("resemblyzer not importable in this venv or the "
                       "coqui-tts side venv (see docs/INSTALL.md)")
    return True, emb.method


ECAPA_METHOD = "speechbrain ECAPA-TDNN (spkrec-ecapa-voxceleb), via {interp}"
ECAPA_METHOD_INPROCESS = "speechbrain ECAPA-TDNN (spkrec-ecapa-voxceleb), in-process"

_ECAPA_RUNNER = """
import json, sys
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier
enc = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="models/spkrec-ecapa-voxceleb")
out = []
for p in sys.argv[1:]:
    signal, sr = torchaudio.load(p)
    if signal.shape[0] > 1:
        signal = signal.mean(dim=0, keepdim=True)
    if sr != 16000:
        signal = torchaudio.functional.resample(signal, sr, 16000)
    emb = enc.encode_batch(signal).squeeze().tolist()
    out.append(emb)
print(json.dumps(out))
"""


def _probe_module(interp: str, module: str) -> bool:
    if not Path(interp).exists():
        return False
    proc = subprocess.run(
        [interp, "-c", f"import {module}"],
        capture_output=True, timeout=300, check=False)
    return proc.returncode == 0


def ecapa_interpreter() -> str | None:
    """Interpreter that can import speechbrain, or None (probed)."""
    candidates = []
    env = os.environ.get("CLONEFORGE_EMBED_PYTHON")
    if env:
        candidates.append(env)
    root = Path(__file__).resolve().parent.parent
    candidates.append(str(root / ".venv-yourtts" / "bin" / "python"))
    candidates.append(sys.executable)
    for cand in candidates:
        if cand == sys.executable:
            try:
                import speechbrain  # noqa: F401

                return cand
            except ImportError:
                continue
        elif _probe_module(cand, "speechbrain"):
            return cand
    return None


class EcapaEmbedder:
    """ECAPA-TDNN speaker embedder — the literature-comparable scorer.

    Published SIM figures for VoxCPM2 / CosyVoice / XTTS-v2 in RVCBench
    use ECAPA-family embeddings; GE2E (resemblyzer) numbers live on a
    different scale and must never be blended with these. This class is
    deliberately a separate scorer with its own method string, columns
    and controls.
    """

    name = "ecapa"

    def __init__(self, interp: str):
        self.interp = interp
        self.method = ECAPA_METHOD.format(interp=interp)

    def embed_many(self, paths: list[str]) -> list[list[float]]:
        if not paths:
            return []
        root = Path(__file__).resolve().parent.parent
        proc = subprocess.run(
            [self.interp, "-c", _ECAPA_RUNNER, *paths],
            capture_output=True, text=True, timeout=1800, check=False,
            stdin=subprocess.DEVNULL, cwd=str(root))
        if proc.returncode != 0:
            raise RuntimeError(
                f"ECAPA subprocess failed: {proc.stderr.strip()[-500:]}")
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("[")]
        if not lines:
            raise RuntimeError("ECAPA subprocess produced no embeddings")
        return json.loads(lines[-1])


def get_ecapa_embedder() -> EcapaEmbedder | None:
    """Return a working ECAPA embedder, or None (→ ECAPA NOT MEASURED)."""
    interp = ecapa_interpreter()
    if interp is None:
        return None
    return EcapaEmbedder(interp)


def ecapa_status() -> tuple[bool, str]:
    emb = get_ecapa_embedder()
    if emb is None:
        return False, ("speechbrain not importable in this venv or the "
                       "coqui-tts side venv (see docs/INSTALL.md)")
    return True, emb.method


def similarity(emb: Embedder, path_a: str, path_b: str) -> float:
    """Cosine similarity between the speaker embeddings of two WAV files."""
    a, b = emb.embed_many([path_a, path_b])
    return cosine_similarity(a, b)


def control_scores(emb: Embedder, reference_wav: str,
                   other_speaker_wav: str) -> dict[str, float]:
    """Sanity controls every similarity proof must show.

    self: the reference embedded against itself — must be ~1.0, or the
    pipeline is broken. different_speaker: a known different speaker
    against the reference — must be clearly lower than a real clone's
    score, or the embedder cannot tell speakers apart on this data.
    """
    ref, other = emb.embed_many([reference_wav, other_speaker_wav])
    return {
        "self": cosine_similarity(ref, ref),
        "different_speaker": cosine_similarity(ref, other),
    }
