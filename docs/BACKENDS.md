# Backend adapters

An adapter is a registry entry (`cloneforge/backends.py`) plus, where
implemented, a runner. In v0.1 exactly three runners are implemented:

- **Piper** (`piper` module) — generates synthetic reference speakers and
  the DSP baseline's base voice. Not a cloner.
- **DSP ProsodyMatch** (`cloneforge/audio.py`) — the built-in baseline:
  autocorrelation F0 + speaking-rate measurement of the reference, Piper
  render, ffmpeg `rubberband` pitch shift + `atempo` pace shift. Every
  applied ratio is returned and printed.
- **YourTTS** (`cloneforge/neural.py`) — a real neural zero-shot cloner,
  verified end-to-end on CPU. It runs in-process when `TTS` is importable,
  otherwise via a dedicated interpreter ($CLONEFORGE_TTS_PYTHON or
  `.venv-yourtts/bin/python`). Environment truth: the original `TTS` 0.22
  package refuses Python 3.12; the maintained fork `coqui-tts[codec]`
  plus `six` works.

All neural adapters are **interface-only in v0.1**: the registry knows each
backend's sample requirements, languages, licences (code and weights
separately), VRAM, strengths and published benchmark figures; detection
(`installed()`) probes for its Python module; the bench harness reports it
as NOT RUN with the reason. This is deliberate: a runner that has not been
executed on this machine is not claimed as working.

## Pace-preservation mode (speech-to-speech)

TTS backends invent timing — none publishes a pace error, so CloneForge
never ranks TTS on pace fidelity. The pace path is voice conversion:

- `cloneforge route --priority pace` ranks the RVC adapter first, with the
  warning printed.
- The RVC adapter interface (`kind="voice-conversion"`) declares its real
  requirements: a per-voice trained model (~10 min of target audio is the
  community norm; registry minimum 60 s is for a smoke test, not quality),
  and a *performed* source take whose timing/hesitations/breath are carried
  into the target voice by construction.
- v0.1 does not wrap RVC's training/inference. Conversion runs in RVC
  itself; CloneForge's job is to route you there honestly instead of
  pretending a TTS clone preserved your pace.

## Adding a backend

1. Add a `Backend` entry with published figures only — every SIM/WER must
   name its benchmark (a test enforces this).
2. Add a probe module/binary.
3. Implement a runner callable in `bench.py`'s runner map and a synth path.
4. Run it end-to-end on this machine class (CPU-only) or mark it GPU-only
   in `notes`. Unrun code does not get a "works" claim.
