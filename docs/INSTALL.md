# Install

## Core (works on a CPU-only machine, ~250 MB)

```bash
git clone https://github.com/example/cloneforge.git   # placeholder remote
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

## Neural backends (each is a separate, optional install)

CloneForge never installs a neural backend for you silently. Run
`cloneforge route` for the pick and its reason, then follow that backend's
own install docs (linked by `cloneforge doctor`). Known environment notes
from the Nov 2026 build:

- **Coqui TTS 0.22 (XTTS-v2 / YourTTS) requires Python < 3.12.** On a
  Python-3.12-only machine the install fails with "No matching
  distribution found". Use the maintained fork package (`coqui-tts`) or a
  Python 3.11 venv. The YourTTS model itself is CPU-runnable once installed.
- XTTS-v2 weights are Coqui Public Model Licence — **non-commercial**,
  whichever fork you install them from.
- dots.tts / VoxCPM2 / Fish S2 expect a serious GPU (their published latency
  figures come from datacentre cards). Routing accounts for this: on a
  CPU-only box, `route --priority speed` prefers CPU-runnable backends.
