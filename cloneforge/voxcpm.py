"""VoxCPM2 runner — the strongest fully-Apache open cloner, run for real.

VoxCPM2 (OpenBMB/VoxCPM, Apache-2.0 code AND weights) is heavy: the
pip package pulls its own torch stack, so CloneForge runs it from a
dedicated side venv (.venv-vox), never the main environment. Interpreter
search order: $CLONEFORGE_VOX_PYTHON, ./.venv-vox/bin/python, then the
current interpreter. Availability is probed (`import voxcpm`), never
guessed; cloning shells out to that interpreter and measures wall-clock
time in the caller.

CPU note (measured, Nov 2026): the model is ~2B parameters. On this
CPU-only VM it is slow and memory-hungry; the bench records the actual
latency and peak behaviour rather than promising real-time use. See
docs/PROOF-2026-11-24-v03.md for what it actually did here.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_RUNNER = """
import sys
import soundfile as sf
from voxcpm import VoxCPM
text, reference, ref_text, out = sys.argv[1:5]
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
kwargs = {"text": text, "cfg_value": 2.0, "inference_timesteps": 10}
if reference:
    kwargs["prompt_wav_path"] = reference
    if ref_text:
        kwargs["prompt_text"] = ref_text
wav = model.generate(**kwargs)
sf.write(out, wav, model.tts_model.sample_rate)
print("ok")
"""

_VOX_INTERP_CACHE: str | None = None
_VOX_INTERP_PROBED = False


def voxcpm_interpreter() -> str | None:
    """Interpreter that can import voxcpm, or None (probed, cached)."""
    global _VOX_INTERP_CACHE, _VOX_INTERP_PROBED
    if _VOX_INTERP_PROBED:
        return _VOX_INTERP_CACHE
    result = None
    candidates = []
    env = os.environ.get("CLONEFORGE_VOX_PYTHON")
    if env:
        candidates.append(env)
    root = Path(__file__).resolve().parent.parent
    candidates.append(str(root / ".venv-vox" / "bin" / "python"))
    candidates.append(sys.executable)
    for cand in candidates:
        if not Path(cand).exists():
            continue
        if cand == sys.executable:
            try:
                import voxcpm  # noqa: F401

                result = cand
                break
            except ImportError:
                continue
        probe = subprocess.run(
            [cand, "-c", "import voxcpm"],
            capture_output=True, timeout=300, check=False)
        if probe.returncode == 0:
            result = cand
            break
    _VOX_INTERP_CACHE = result
    _VOX_INTERP_PROBED = True
    return result


def voxcpm_available() -> tuple[bool, str]:
    interp = voxcpm_interpreter()
    if interp:
        return True, f"voxcpm importable via {interp}"
    return False, ("voxcpm not installed in any known venv "
                   "(see docs/INSTALL.md: pip install voxcpm into .venv-vox)")


def voxcpm_clone(text: str, reference_wav: str | Path, out_wav: str | Path,
                 reference_text: str | None = None) -> dict:
    """Clone `reference_wav`'s voice reading `text`, with VoxCPM2.

    When the reference transcript is known it is passed as prompt_text
    (VoxCPM's continuation mode — its strongest cloning path); without a
    transcript the reference is used as a style prompt only.
    """
    interp = voxcpm_interpreter()
    if interp is None:
        raise RuntimeError(
            "VoxCPM2 unavailable: no interpreter with `voxcpm` importable. "
            "Install it into a side venv: python -m venv .venv-vox && "
            ".venv-vox/bin/pip install voxcpm (see docs/INSTALL.md).")
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [interp, "-c", _RUNNER, text, str(reference_wav),
         reference_text or "", str(out)],
        capture_output=True, text=True, timeout=3600, check=False,
        stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(
            f"VoxCPM2 subprocess failed (rc={proc.returncode}): "
            f"{proc.stderr.strip()[-800:]}")
    if not out.exists():
        raise RuntimeError("VoxCPM2 reported success but produced no file")
    return {"backend": "voxcpm2", "output_path": str(out), "via": interp}
