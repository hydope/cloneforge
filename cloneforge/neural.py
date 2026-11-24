"""Neural backend runners that CloneForge has actually executed.

YourTTS (via the maintained `coqui-tts` fork) is the one neural cloner
verified end-to-end on a CPU-only Python 3.12 machine in Nov 2026:

- the original `TTS==0.22.0` package cannot install on Python 3.12
  (Requires-Python <3.12 — pip finds no matching distribution);
- the fork package `coqui-tts` (0.28.0) installs and runs, with two
  additions: `coqui-tts[codec]` and the `six` package;
- torch must be the CPU build (PyPI's default torchaudio wheel is a CUDA
  build on some platforms and fails to load).

Because those dependencies are heavy, YourTTS usually lives in its own
venv. This module runs it in-process when `TTS` is importable here, and
otherwise shells out to a dedicated interpreter, found via (in order):
$CLONEFORGE_TTS_PYTHON, ./.venv-yourtts/bin/python, ./.venv/bin/python.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_RUNNER = """
import sys
from TTS.api import TTS
text, reference, language, out = sys.argv[1:5]
tts = TTS("tts_models/multilingual/multi-dataset/your_tts", progress_bar=False)
tts.tts_to_file(text=text, speaker_wav=reference, language=language,
                file_path=out)
print("ok")
"""

_XTTS_RUNNER = """
import sys
from TTS.api import TTS
text, reference, language, out = sys.argv[1:5]
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
tts.tts_to_file(text=text, speaker_wav=reference, language=language,
                file_path=out)
print("ok")
"""

XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def tts_interpreter() -> str | None:
    """Interpreter that can import TTS, or None (checked, not guessed)."""
    candidates = []
    env = os.environ.get("CLONEFORGE_TTS_PYTHON")
    if env:
        candidates.append(env)
    root = Path(__file__).resolve().parent.parent
    candidates.append(str(root / ".venv-yourtts" / "bin" / "python"))
    candidates.append(sys.executable)
    for cand in candidates:
        if not Path(cand).exists():
            continue
        probe = subprocess.run(
            [cand, "-c", "import TTS"],
            capture_output=True, timeout=120, check=False)
        if probe.returncode == 0:
            return cand
    return None


def yourtts_available() -> tuple[bool, str]:
    interp = tts_interpreter()
    if interp:
        return True, f"TTS importable via {interp}"
    return False, ("coqui-tts not installed in any known venv "
                   "(see docs/INSTALL.md: Python 3.12 needs the fork)")


def yourtts_clone(text: str, reference_wav: str | Path, out_wav: str | Path,
                  language: str = "en") -> dict:
    """Clone `reference_wav`'s voice reading `text`, with YourTTS on CPU."""
    interp = tts_interpreter()
    if interp is None:
        raise RuntimeError(
            "YourTTS unavailable: no interpreter with `TTS` importable. "
            "Install the fork: pip install 'coqui-tts[codec]' six "
            "(original TTS 0.22 does not support Python 3.12).")
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    if interp == sys.executable:
        from TTS.api import TTS

        tts = TTS("tts_models/multilingual/multi-dataset/your_tts",
                  progress_bar=False)
        tts.tts_to_file(text=text, speaker_wav=str(reference_wav),
                        language=language, file_path=str(out))
    else:
        proc = subprocess.run(
            [interp, "-c", _RUNNER, text, str(reference_wav), language, str(out)],
            capture_output=True, text=True, timeout=900, check=False,
            stdin=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise RuntimeError(
                f"YourTTS subprocess failed: {proc.stderr.strip()[-500:]}")
    if not out.exists():
        raise RuntimeError("YourTTS reported success but produced no file")
    return {"backend": "yourtts", "output_path": str(out), "via": interp}


def xtts_available() -> tuple[bool, str]:
    """Same interpreter probe as YourTTS — XTTS ships in the same fork."""
    return yourtts_available()


def xtts_clone(text: str, reference_wav: str | Path, out_wav: str | Path,
               language: str = "en") -> dict:
    """Clone `reference_wav`'s voice reading `text`, with XTTS-v2 on CPU.

    The XTTS-v2 weights are under the Coqui Public Model Licence
    (non-commercial). Downloading them requires accepting that licence;
    the coqui-tts fork records acceptance via the COQUI_TOS_AGREED=1
    environment variable (TTS/utils/manage.py — verified in the installed
    0.28.0 source; without it the loader blocks forever on an interactive
    input() prompt). CloneForge sets it ONLY for the local test
    subprocess and flags it here and in docs/BACKENDS.md. Using XTTS
    output commercially is not licensed, whatever this code does.
    """
    interp = tts_interpreter()
    if interp is None:
        raise RuntimeError(
            "XTTS-v2 unavailable: no interpreter with `TTS` importable. "
            "Install the fork: pip install 'coqui-tts[codec]' six "
            "(original TTS 0.22 does not support Python 3.12).")
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, COQUI_TOS_AGREED="1", COQ_TOS_AGREED="1")
    if interp == sys.executable:
        os.environ.setdefault("COQUI_TOS_AGREED", "1")
        from TTS.api import TTS

        tts = TTS(XTTS_MODEL, progress_bar=False)
        tts.tts_to_file(text=text, speaker_wav=str(reference_wav),
                        language=language, file_path=str(out))
    else:
        proc = subprocess.run(
            [interp, "-c", _XTTS_RUNNER, text, str(reference_wav),
             language, str(out)],
            capture_output=True, text=True, timeout=1800, check=False,
            env=env, stdin=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise RuntimeError(
                f"XTTS-v2 subprocess failed: {proc.stderr.strip()[-500:]}")
    if not out.exists():
        raise RuntimeError("XTTS-v2 reported success but produced no file")
    return {"backend": "xtts2", "output_path": str(out), "via": interp,
            "licence_note": "weights: Coqui Public Model Licence "
                            "(non-commercial); COQUI_TOS_AGREED=1 was set "
                            "for the local test subprocess"}
