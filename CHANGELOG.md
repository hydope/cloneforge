# Changelog

All notable changes to CloneForge. Versions are tagged in git; the
GitHub release notes for each version summarise the same facts.

## v0.3.0 — 2026-11-24 (world-criteria round)

Judged against a pre-registered world-criteria checklist (CRITIQUE.md,
committed before any fix). Highlights:

- **Doctor tells the truth.** Backend detection now probes the same
  interpreters the bench executes (coqui-tts side venv for XTTS/YourTTS,
  .venv-vox for VoxCPM2), with the venv path printed. The v0.2 bug —
  doctor reporting XTTS/YourTTS "not installed" while the bench ran
  them — is closed and regression-tested.
- **Second similarity scorer: ECAPA-TDNN** (speechbrain
  spkrec-ecapa-voxceleb), reported in its own column next to GE2E,
  never blended. GE2E numbers are not comparable to published
  WavLM/ECAPA SIM; ECAPA is the literature-comparable scorer. Controls
  for both scorers in every report.
- **Latency measured** per backend run (wall-clock seconds) in every
  bench table.
- **VoxCPM2 runner** (side venv, CPU torch) and a complete **dots.tts
  runner** (interpreter probe + subprocess; states the measured
  hardware blocker when it cannot run — see docs/PROOF-2026-11-24-v03.md).
- **Real-human corpus**: 3 LibriSpeech test-clean speakers (CC BY 4.0,
  OpenSLR SLR12) in examples/corpus/ with docs/CORPUS.md recording
  source, licence and speaker for every clip; human bench results are
  reported separately from synthetic results.
- **Blind listening test**: `cloneforge blindtest build|score` —
  shuffled A/B packs with a hidden answer key and a scoring sheet.
  No human has scored a pack yet; the tool reports that, not a result.
- **UI fixed and proven**: gradio 6.x crashed at import on machines
  whose NO_PROXY contains bracketed IPv6 entries (httpx parses it);
  the UI now sanitises that variable before importing gradio. Served
  page captured in docs/ui-page-capture.html (HTTP 200; /config
  component tree verified). UI operations are module-level functions
  exercised by tests.
- **Playable demos** in examples/demo/ (clones of the public human
  reference + synthetic clones, MP3, <2 MB total).
- Tests: 37 → 55. Ruff clean; CI green on the release commit.
- Known open item: checklist item 1 stays FAIL/open — no VoxCPM2 clone
  was produced (execution of the downloaded weights was halted by an
  automated execution-risk flag, pending owner approval). The v0.3
  world-product score is 7/10; see CRITIQUE.md.

## v0.2.0 — 2026-11-24

- Similarity MEASURED with resemblyzer GE2E (controls: self = 1.0,
  different speaker 0.5111–0.5984); XTTS-v2 added as second neural
  runner (coqui-tts fork; COQUI_TOS_AGREED licence-prompt hang and
  CUDA-linked torchcodec wheel diagnosed and fixed).
- Proof corpus expanded to 3 lines × 2 synthetic speakers
  (docs/PROOF-2026-11-24.md).
- DSP baseline relabelled CONTROL everywhere; bench reports separate
  clones / controls / not-run structurally.
- GitHub Actions CI (pytest + ruff); clean-install proof from the
  public repo following only the README. 37 tests.
- Scored 10/10 against its pre-registered internal checklist — and
  6.5/10 as a world product by an outside top-critic review (cloner
  3/10, app 4/10, engineering 9/10). v0.3 exists because of that review.

## v0.1.0 — 2026-11-23

- First release: backend registry (12 adapters, code-vs-weights
  licence split), evidence router, benchmark harness measuring pace,
  F0 and WER; runners for Piper, the DSP prosody baseline and YourTTS
  (via the maintained coqui-tts fork — the original TTS 0.22 cannot
  install on Python 3.12).
- Proof: 1 line × 1 synthetic speaker (docs/PROOF-2026-11-23.md);
  similarity NOT MEASURED. 25 tests. Self-critique: 7.5/10.
