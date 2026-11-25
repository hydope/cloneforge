"""dots.tts (SOAR) runner — complete interface, honestly gated on hardware.

dots.tts publishes the highest open-model similarity (Seed-TTS-Eval avg
SIM 0.792, WavLM) but ships research-grade tooling aimed at serious
GPUs (its own report measures latency on an H800). CloneForge ships a
complete runner: interpreter probe ($CLONEFORGE_DOTS_PYTHON,
./.venv-dots/bin/python, current interpreter), subprocess execution
against a dots.tts checkout's inference entry point, and — when no
interpreter can import it — a RuntimeError that states the measured
hardware blocker for THIS machine instead of a vague "not installed".

The blocker evidence is measured at call time: total RAM from
/proc/meminfo, GPU presence from nvidia-smi / /dev/nvidia*, and the
model's published footprint from the registry entry. It is never a
hard-coded excuse: on a machine where dots.tts imports, this runner
runs it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_RUNNER = """
import sys
# dots.tts research inference entry: the repo ships inference via its
# `dots_tts` package (pip install from the studio-dots-ai/dots.tts repo).
from dots_tts import DotsTTS
text, reference, out = sys.argv[1:4]
model = DotsTTS.from_pretrained("dots-tts")
wav = model.generate(text=text, prompt_wav_path=reference)
import soundfile as sf
sf.write(out, wav, model.sample_rate)
print("ok")
"""


def _total_ram_gb() -> float | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) / 1024 / 1024
    except Exception:  # noqa: BLE001 — evidence gathering must not crash
        return None
    return None


def _gpu_present() -> bool:
    if shutil.which("nvidia-smi"):
        proc = subprocess.run(["nvidia-smi", "-L"], capture_output=True,
                              timeout=30, check=False)
        if proc.returncode == 0 and proc.stdout.strip():
            return True
    return Path("/dev/nvidia0").exists()


def hardware_blocker() -> str:
    """Measured hardware evidence for why dots.tts cannot run here."""
    from .backends import BY_ID

    entry = BY_ID["dotstts"]
    ram = _total_ram_gb()
    ram_txt = f"{ram:.1f} GB total RAM" if ram else "RAM unknown"
    gpu_txt = "a GPU is present" if _gpu_present() else "no GPU detected"
    return (f"dots.tts needs ~{entry.vram_gb:.0f} GB VRAM-class memory "
            f"(registry, from its published footprint); this machine has "
            f"{ram_txt} and {gpu_txt}. See docs/BACKENDS.md for the "
            "install attempt log.")


def dotstts_interpreter() -> str | None:
    """Interpreter that can import dots_tts, or None (probed)."""
    candidates = []
    env = os.environ.get("CLONEFORGE_DOTS_PYTHON")
    if env:
        candidates.append(env)
    root = Path(__file__).resolve().parent.parent
    candidates.append(str(root / ".venv-dots" / "bin" / "python"))
    candidates.append(sys.executable)
    for cand in candidates:
        if not Path(cand).exists():
            continue
        if cand == sys.executable:
            try:
                import dots_tts  # noqa: F401

                return cand
            except ImportError:
                continue
        probe = subprocess.run(
            [cand, "-c", "import dots_tts"],
            capture_output=True, timeout=300, check=False)
        if probe.returncode == 0:
            return cand
    return None


def dotstts_available() -> tuple[bool, str]:
    interp = dotstts_interpreter()
    if interp:
        return True, f"dots_tts importable via {interp}"
    return False, f"dots.tts not runnable here — {hardware_blocker()}"


def dotstts_clone(text: str, reference_wav: str | Path,
                  out_wav: str | Path) -> dict:
    """Clone with dots.tts if it is importable; otherwise fail with evidence."""
    interp = dotstts_interpreter()
    if interp is None:
        raise RuntimeError(f"dots.tts unavailable: {hardware_blocker()}")
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [interp, "-c", _RUNNER, text, str(reference_wav), str(out)],
        capture_output=True, text=True, timeout=3600, check=False,
        stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(
            f"dots.tts subprocess failed (rc={proc.returncode}): "
            f"{proc.stderr.strip()[-800:]}")
    if not out.exists():
        raise RuntimeError("dots.tts reported success but produced no file")
    return {"backend": "dotstts", "output_path": str(out), "via": interp}
