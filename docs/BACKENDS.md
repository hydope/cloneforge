# Backend adapters

An adapter is a registry entry (`cloneforge/backends.py`) plus, where
implemented, a runner.

## v0.3 additions

- **VoxCPM2** (`cloneforge/voxcpm.py`) — runner implemented (side venv
  `.venv-vox`, CPU torch, continuation mode with the reference
  transcript). Status in the v0.3 proof: **NOT RUN — execution of the
  downloaded model was halted by an automated execution-risk flag on
  the model files, and the run was not attempted without the owner's
  approval.** The weights download itself reached 311,734,174 of
  ~4.58 GB for model.safetensors (plus a 0.38 GB audiovae.pth) before
  being stopped; install of the `voxcpm` 2.0.3 package and CPU torch
  2.15.0+cpu into .venv-vox succeeded and is logged in
  docs/PROOF-2026-11-24-v03.md. The runner stays in the registry behind
  the operator kill-switch ($CLONEFORGE_DISABLE_BACKENDS) until the
  owner approves executing it.
- **dots.tts** (`cloneforge/dotstts.py`) — runner implemented and
  unit-tested with a mocked backend. **Blocked with hard evidence**:
  dots.tts is a 2B-parameter GPU model; its own README (read
  2026-11-25) tabulates a measured serving memory footprint of
  5.65 GB at the smallest bucket (<64 patches), 6.53 GB (<128),
  7.86 GB (<256) and 10.51 GB (<512), and all its published
  performance figures are measured on 1× NVIDIA H100. This machine,
  measured the same day: 8,124,900 kB total RAM (`/proc/meminfo`
  MemTotal ≈ 7.7 GiB usable), no GPU (`nvidia-smi` not found, no
  /dev/nvidia*). Additionally, the cloned dots.tts repository was
  flagged by an automated execution-risk check in this session, so its
  code was read as text only and never installed or executed. The
  bench prints this blocker verbatim from
  `dotstts.hardware_blocker()`, which measures RAM and GPU presence at
  runtime rather than assuming them.
- **ECAPA-TDNN scorer** (`cloneforge/similarity.py`, speechbrain
  spkrec-ecapa-voxceleb) — second, literature-comparable similarity
  scorer alongside GE2E; see "Similarity measurement" below.
- **Doctor truth fix** — `Backend.status()` and the bench runner
  registry (`bench.runner_availability()`) now consult the same
  interpreter probes, so what doctor calls INSTALLED is exactly what
  the bench can execute; regression-tested.

## v0.2 runners

In v0.2 exactly four runners were implemented:

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

Two independent scorers, reported in separate columns, never blended:

- **GE2E** — `cloneforge/similarity.py` wraps resemblyzer's VoiceEncoder
  (GE2E, 256-dim). GE2E cosines run high (clones 0.75–0.92 in our
  benches) and are **not comparable** to the SIM figures published for
  WavLM/ECAPA-based evaluations.
- **ECAPA-TDNN** — speechbrain `spkrec-ecapa-voxceleb` (192-dim),
  the architecture family used by Seed-TTS-Eval-style SIM reporting;
  this is the literature-comparable column. Its cosines run lower and
  separate speakers harder (different-speaker controls 0.11–0.16 in the
  v0.3 human bench vs GE2E's 0.54–0.55).

Both run in-process when importable, else by subprocess in the
coqui-tts side venv (reusing its torch). Every bench report names both
methods and shows sanity controls for each: reference-vs-itself (must
be ~1.0) and a different-speaker CONTROL voice vs the reference (must
be clearly lower than the clones). If a scorer is unreachable, its
column is NOT MEASURED — never estimated.

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
