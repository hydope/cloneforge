# Install

## Core (works on a CPU-only machine, ~250 MB)

```bash
git clone https://github.com/hydope/cloneforge.git   # placeholder remote
cd cloneforge
./install.sh
```

`install.sh` creates `.venv`, installs CloneForge + Piper + numpy, and
downloads two Piper test voices (amy = base voice, lessac = synthetic
reference speaker) into `models/` (~63 MB each, from
https://huggingface.co/rhasspy/piper-voices). Models are git-ignored;
they are test fixtures, not part of the project.

Manual equivalent:

```bash
python3 -m venv .venv
.venv/bin/pip install -e . numpy piper-tts
# download en_US-amy-medium.onnx{,.json} and en_US-lessac-medium.onnx{,.json}
# from rhasspy/piper-voices into models/
.venv/bin/cloneforge doctor
```

## Optional extras

| Extra | Command | What it unlocks |
|---|---|---|
| Measured WER | `.venv/bin/pip install faster-whisper` | bench transcribes outputs locally and scores pronunciation |
| Measured similarity | `.venv/bin/pip install resemblyzer` | bench computes speaker-embedding cosine |
| Gradio UI | `.venv/bin/pip install 'cloneforge[ui]'` | `cloneforge ui` |
| Dev | `.venv/bin/pip install -e '.[dev]'` | pytest + ruff |

Measured similarity also works if resemblyzer is installed in the
coqui-tts side venv (`.venv-yourtts`) instead of the main venv — the
bench finds it there and calls it by subprocess, reusing that venv's
torch rather than installing a second one. That is how the 2026-11-24
proof was measured. Override the search with `$CLONEFORGE_EMBED_PYTHON`.

## v0.3 extras

**ECAPA scorer (speechbrain)** — the second, literature-comparable
similarity scorer. Install into the coqui-tts side venv (where the
embedders run):

```bash
.venv-yourtts/bin/pip install speechbrain   # 1.1.2 verified
```

Its weights (spkrec-ecapa-voxceleb) download from HuggingFace on first
use into `models/spkrec-ecapa-voxceleb/`.

**VoxCPM2 (optional, .venv-vox)** — CPU torch MUST come from the
PyTorch CPU index; a default `pip install voxcpm` pulls ~2.5 GB of
CUDA wheels a CPU-only machine cannot use (observed in the v0.3
round):

```bash
python3 -m venv .venv-vox
.venv-vox/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
.venv-vox/bin/pip install voxcpm            # 2.0.3 verified
```

The VoxCPM2 weights (~4.96 GB total: model.safetensors 4.58 GB +
audiovae.pth 0.38 GB) download from HuggingFace on first generation.
The download was observed stalling under the xet transfer backend
when two clients shared the cache; `HF_HUB_DISABLE_XET=1` (classic
resumable HTTP) progressed at ~2.5 MB/s. NOTE: in the v0.3 round,
actually *executing* the downloaded model was halted by an automated
execution-risk flag and not attempted without the owner's approval —
see docs/PROOF-2026-11-24-v03.md. The runner can be disabled with
$CLONEFORGE_DISABLE_BACKENDS=voxcpm2.

**Gradio UI gotcha** — gradio 6.x parses the process environment at
import; an NO_PROXY value containing a bracketed IPv6 entry such as
`[::1]` crashes httpx (`Invalid port: ':1]'`) before the UI starts.
`cloneforge ui` sanitises NO_PROXY/no_proxy before importing gradio,
so no user action is needed; the failure and fix are recorded in
docs/PROOF-2026-11-24-v03.md.

## Clean-install proof (2026-11-24, recorded)

A fresh clone of the public repo into an empty directory, built by
following ONLY the instructions above:

1. `git clone https://github.com/hydope/cloneforge.git` — OK
2. `./install.sh` — OK (venv, core deps, both Piper voices)
3. `.venv/bin/cloneforge doctor` — OK; correctly reported the speaker
   embedder as not installed (a fresh clone has no side venv) instead
   of guessing
4. `cloneforge reference` + `cloneforge synth` (DSP CONTROL) — OK,
   produced a 3.30 s clone.wav for the proof line and printed the
   CONTROL — not a voice clone label
5. `pip install -e '.[dev]'` then `pytest` — **37 passed**; `ruff check`
   — clean

Any instruction that had failed would have been fixed and re-tested
before this was written; none did.

Re-verified the same day against the final v0.2 tree (fresh clone,
workspace scratch dir): install.sh OK, doctor OK (0.2.0), reference +
synth OK with the CONTROL label printed, **37 passed**, ruff clean.
One environment lesson from that run: pip unpacks wheels in `$TMPDIR`
(default `/tmp`); on a machine whose `/tmp` is a small tmpfs the core
install can die with a misleading `No space left on device` even with
plenty of disk free. If you hit it, re-run with a roomy TMPDIR, e.g.
`TMPDIR=~/tmp ./install.sh` (with `~/tmp` created first).

## Neural backends (each is a separate, optional install)

CloneForge never installs a neural backend for you silently. Run
`cloneforge route` for the pick and its reason, then follow that backend's
own install docs (linked by `cloneforge doctor`). Known environment notes
from the Nov 2026 build:

- **Coqui TTS 0.22 (XTTS-v2 / YourTTS) requires Python < 3.12.** On a
  Python-3.12-only machine the install fails with "No matching
  distribution found". Use the maintained fork package (`coqui-tts`) or a
  Python 3.11 venv. The YourTTS model itself is CPU-runnable once installed.
- **XTTS-v2 + CPU torch: torchcodec must come from the PyTorch CPU index.**
  With torch 2.11.0+cpu, the PyPI torchcodec 0.17 wheel links against CUDA
  libraries (`libc10_cuda.so`, `libnvrtc.so.13`) that a CPU install does
  not have, and every `torchaudio.load` — which XTTS uses for the speaker
  reference — dies with `OSError: Could not load this library:
  libtorchcodec_image.so`. Fix, verified 2026-11-24:
  `pip install --force-reinstall torchcodec==0.17.0 --index-url https://download.pytorch.org/whl/cpu`
- **XTTS-v2 licence prompt hangs headless runs.** The fork's model loader
  calls `input()` unless `COQUI_TOS_AGREED=1` is set (verified in the
  installed `TTS/utils/manage.py`). CloneForge sets it for its local test
  subprocess and closes stdin so a prompt can never block a bench.
- XTTS-v2 weights are Coqui Public Model Licence — **non-commercial**,
  whichever fork you install them from.
- dots.tts / VoxCPM2 / Fish S2 expect a serious GPU (their published latency
  figures come from datacentre cards). Routing accounts for this: on a
  CPU-only box, `route --priority speed` prefers CPU-runnable backends.
