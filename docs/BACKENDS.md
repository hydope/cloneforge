# Backend adapters

An adapter is a registry entry (`cloneforge/backends.py`) plus, where
implemented, a runner. In v0.2 exactly four runners are implemented:

- **Piper** (`piper` module) — generates synthetic reference speakers and
  the DSP CONTROL's base voice. Not a cloner; a CONTROL in bench reports.
- **DSP ProsodyMatch** (`cloneforge/audio.py`) — a **CONTROL, not a voice
  clone**: autocorrelation F0 + speaking-rate measurement of the
  reference, Piper render, ffmpeg `rubberband` pitch shift + `atempo`
  pace shift. Every applied ratio is returned and printed. Bench reports
  file it under CONTROLS, never under clones.
- **YourTTS** (`cloneforge/neural.py`) — a real neural zero-shot cloner,
  verified end-to-end on CPU. It runs in-process when `TTS` is importable,
  otherwise via a dedicated interpreter ($CLONEFORGE_TTS_PYTHON or
  `.venv-yourtts/bin/python`). Environment truth: the original `TTS` 0.22
  package refuses Python 3.12; the maintained fork `coqui-tts[codec]`
  plus `six` works.
- **XTTS-v2** (`cloneforge/neural.py`, same fork + side venv) — second
  neural cloner, verified end-to-end on CPU in v0.2
  (docs/PROOF-2026-11-24.md). Two environment traps, both documented in
  docs/INSTALL.md: the loader blocks on an interactive licence prompt
  unless `COQUI_TOS_AGREED=1` is set, and `torchaudio.load` dies unless
  torchcodec comes from the PyTorch CPU index when torch is a CPU build.
  Weights are Coqui Public Model Licence — non-commercial.

The remaining neural adapters are **interface-only in v0.2**: the registry
knows each backend's sample requirements, languages, licences (code and
weights separately), VRAM, strengths and published benchmark figures;
detection (`installed()`) probes for its Python module; the bench harness
reports it as NOT RUN with the reason. This is deliberate: a runner that
has not been executed on this machine is not claimed as working.

## Similarity measurement

`cloneforge/similarity.py` wraps resemblyzer's VoiceEncoder (GE2E,
256-dim). It runs in-process when importable, else by subprocess in the
coqui-tts side venv (reusing its torch). Every bench report names the
method and shows two sanity controls: reference-vs-itself (must be ~1.0)
and a different-speaker CONTROL voice vs the reference (must be clearly
lower than the clones). If no embedder is reachable, similarity is
reported NOT MEASURED — never estimated.

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
