# CloneForge

**A free, local, open-source voice-cloning *meta-engine* — not another model.**

Every famous voice-cloning repo is one model, with one model's ceiling, one
licence trap, and no way to know whether it was actually the right tool for
your voice, your language, or your reference length. CloneForge is the layer
above them:

1. **Router** — routes your job to the best *installed* free backend, using
   published benchmark evidence, and explains the pick in writing
   (`cloneforge route`).
2. **Benchmark harness** — the product none of the 20 ship: run the *same
   line* through every runnable backend and get **measured** pace
   (speaking-rate difference), pitch, pronunciation (WER via local ASR) and
   speaker similarity (local embedding cosine). Anything that cannot be
   measured is printed as **NOT MEASURED**. CloneForge never invents a
   quality number (`cloneforge bench`).
3. **Licence clarity** — code and weights licences are tracked *separately*
   for every backend, because "MIT repo" F5-TTS ships CC-BY-NC weights and
   XTTS-v2 ships non-commercial CPML weights. The router excludes them from
   commercial jobs automatically.
4. **Honesty about languages** — Urdu (and any language with no published
   cloning accuracy) is flagged **UNVERIFIED**, with a listening-test flow
   recommended instead of a fake ranking.
5. **Privacy** — everything runs locally. Your reference audio never leaves
   your machine. Test fixtures are *synthetic* speakers generated on-device;
   CloneForge ships no real person's voice.

## Quick start

```bash
git clone https://github.com/example/cloneforge.git   # placeholder — set your remote
cd cloneforge
./install.sh                     # venv + core deps + Piper test voices
.venv/bin/cloneforge doctor      # what is installed, what is not, and why
```

Generate a synthetic test speaker, clone it with the built-in baseline, and
benchmark everything runnable:

```bash
LINE="The quick brown fox jumps over the lazy dog near the river bank."
.venv/bin/cloneforge reference --text "$LINE" --out examples/output/reference.wav
.venv/bin/cloneforge synth     --text "$LINE" --reference examples/output/reference.wav \
                               --out examples/output/clone-dsp.wav
.venv/bin/cloneforge bench     --text "$LINE" --reference examples/output/reference.wav \
                               --out-dir examples/output/bench
```

Route a real job (no audio is processed — this is the decision layer):

```bash
.venv/bin/cloneforge route --lang en --sample 8 --priority accuracy
.venv/bin/cloneforge route --lang ur --sample 30    # ← watch the UNVERIFIED flag
.venv/bin/cloneforge route --lang en --sample 30 --priority pace
.venv/bin/cloneforge route --lang en --sample 30 --commercial
```

Optional: local ASR for measured WER (`pip install faster-whisper`),
a speaker embedder for measured similarity (`pip install resemblyzer`),
and a Gradio UI (`pip install 'cloneforge[ui]'`, then `cloneforge ui`).

## Backends (adapters)

| Backend | Published evidence | Min sample | Commercial? | Status in CloneForge |
|---|---|---|---|---|
| dots.tts (SOAR) | SIM 0.792, WER 2.95% (Seed-TTS-Eval) | ~3 s | ✅ Apache/Apache | adapter, interface-only runner |
| VoxCPM2 | SIM 0.753, WER 1.84% (Seed-TTS-Eval) | ~3 s | ✅ Apache/Apache | adapter, interface-only runner |
| Fish Speech S2 | WER 0.99% EN (vendor report) | 10 s | ❌ research weights | adapter, interface-only runner |
| CosyVoice 3 | SIM 0.718, WER 2.02% | 3 s | ✅ Apache/Apache | adapter, interface-only runner |
| F5-TTS | SIM 0.670, WER 2.00% | 3 s | ❌ CC-BY-NC weights | adapter, interface-only runner |
| Higgs Audio V2 | best open emotion (EmergentTTS 75.7%) | 3 s | ❌ non-commercial | adapter, interface-only runner |
| XTTS-v2 (idiap fork) | SIM 0.45 (RVCBench, ECAPA) | 6 s | ❌ CPML weights | adapter, interface-only runner |
| YourTTS | short-sample specialist, CPU | 3 s | ✅ | **runs** (via coqui-tts fork venv, verified) |
| OpenVoice v2 | SIM 0.24 (RVCBench, ECAPA) | 3 s | ✅ MIT/MIT | adapter, interface-only runner |
| GPT-SoVITS | few-shot from ~1 min | 5 s | ✅ MIT/MIT | adapter, interface-only runner |
| RVC | pace/emotion preserved by construction (STS) | ~60 s train | ✅ | interface-only (conversion runs in RVC) |
| Piper | — (not a cloner) | — | ✅ | **runs**: synthetic references + DSP base voice |
| DSP ProsodyMatch | built-in baseline | 2 s | ✅ | **runs**: measured pace/pitch matching |

Full per-backend notes: [docs/BACKENDS.md](docs/BACKENDS.md).

## CloneForge vs the top 20 voice-cloning repos

Stars are GitHub stars from Nov 2026 research. "Bench harness" means a
user-facing tool that runs *multiple* backends on the same line and scores
them — publishing a results table in a paper is not a harness.

| Project | ★ | One model only? | Bench harness | Measures pace | Licence split shown | Local/private | Free | Urdu honesty |
|---|---|---|---|---|---|---|---|---|
| **CloneForge** | new | **No — routes 12** | **Yes — measured, or NOT MEASURED** | **Yes — rate diff %** | **Yes, per backend** | Yes | Yes (MIT) | **Flags UNVERIFIED** |
| VoiceStudio | 117,201 | No (app shell) | No | No | Partial | Yes | Yes | No Urdu evidence |
| voicebox | 61,216 | No (app shell) | No | No | Partial | Yes | Yes | No Urdu evidence |
| Real-Time-Voice-Cloning | 60,246 | Yes (SV2TTS) | No | No | No | Yes | Yes | No |
| VibeVoice | 57,519 | Yes | No | No | No | Yes | Yes | No |
| coqui-ai/TTS (XTTS) | 46,272 | Toolkit | No | No | **No — CPML hidden in fine print** | Yes | Yes | No |
| VoxCPM | 42,922 | Yes | Publishes results only | No | Yes (Apache) | Yes | Yes | No |
| ChatTTS | 40,034 | Yes (not a cloner) | No | No | No | Yes | Yes | No |
| Bark | 39,421 | Yes | No | No | No | Yes | Yes | No |
| RVC-WebUI | 39,274 | Yes (conversion) | No | Preserves, doesn't measure | Yes (MIT) | Yes | Yes | Language-agnostic (STS) |
| OpenVoice | 38,314 | Yes | No | No | Yes (MIT) | Yes | Yes | No |
| MockingBird | 36,857 | Yes | No | No | No | Yes | Yes | No |
| fish-speech | 33,845 | Yes | Publishes results only | No | Partial (research weights) | Yes | Yes | No |
| Chatterbox | 28,059 | Yes | No | No | Yes (MIT) | Yes | Yes | No — **retired Aug 2026** |
| so-vits-svc | 28,022 | Yes (conversion) | No | Preserves, doesn't measure | No | Yes | Yes | Language-agnostic (STS) |
| IndexTTS | 25,256 | Yes | Publishes results only | No | Partial | Yes | Yes | No |
| CosyVoice | 24,492 | Yes | Publishes results only | No | Yes (Apache) | Yes | Yes | No (not supported) |
| OmniVoice | 16,779 | Yes | No | No | Partial | Yes | Yes | Research Urdu fine-tunes exist, unverified |
| F5-TTS | 15,644 | Yes | Publishes results only | No | **No — MIT badge, CC-BY-NC weights** | Yes | Yes | No (not supported) |
| Higgs Audio | 8,390 | Yes | Publishes results only | No | Partial | Yes | Yes | No |
| dots.tts | 1,435 | Yes | Publishes results only | No | Yes (Apache) | Yes | Yes | No (not in test set) |

## What CloneForge does NOT claim

- **No new model.** CloneForge trains nothing. Its neural backends' quality
  ceilings are *their* published numbers, not ours.
- **No 100% accuracy.** No tool verifiably achieves it: a real recording
  scores only ~0.734 speaker similarity against another real recording of
  the same person, and no TTS system publishes a pace/duration error at all.
- **No Urdu verification.** No top tool publishes Urdu cloning SIM/WER/
  prosody evidence. CloneForge flags this instead of hiding it.
- **TTS does not preserve pace.** Text-to-speech invents new timing. Only
  speech-to-speech conversion (the RVC path) preserves a real performance's
  pace and emotion — and in v0.1 that path is an interface, not a wrapper.
- **The built-in DSP baseline is a baseline.** It measurably matches pace
  and pitch; its speaker similarity is low, and the bench report will show
  you exactly how low once an embedder is installed — or say NOT MEASURED.

## Measured proof (this build, CPU-only, synthetic speaker)

From `docs/PROOF-2026-11-23.md` (full bench report, committed) — the
reference is a synthetic Piper speaker, the line is the pangram in the
quick start, and every number was measured on a CPU-only machine:

| Backend | Pace (rate diff) | Pitch (F0 diff) | WER (local ASR) |
|---|---|---|---|
| DSP ProsodyMatch (built-in) | **+0.05%** | +0.86% | 0.00% |
| YourTTS (real neural clone, coqui-tts fork) | −7.08% | −3.53% | 15.38% |
| Piper (unshifted control) | −27.99% | +3.54% | 0.00% |

Read that table carefully: the DSP baseline "winning" pace is exactly the
point of the harness — pace is *measurable and matchable* without any neural
model, while speaker similarity (the thing neural models are actually for)
is reported as **NOT MEASURED** on this machine because no local embedder
was installed. Nothing estimated, nothing hidden.

## Licence

MIT for CloneForge's own code. Backends keep their own licences — the
registry and `cloneforge doctor` surface them before you install anything.

## Ethics

Clone only voices you own or have explicit consent to clone. CloneForge's
fixtures are synthetic for a reason.
