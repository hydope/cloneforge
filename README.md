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
git clone https://github.com/hydope/cloneforge.git
cd cloneforge
./install.sh                     # venv + core deps + Piper test voices
.venv/bin/cloneforge doctor      # what is installed, what is not, and why
```

Generate a synthetic test speaker, run the built-in CONTROL baseline
(a prosody-matched baseline — not a voice clone), and benchmark
everything runnable:

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
| XTTS-v2 (idiap fork) | SIM 0.45 (RVCBench, ECAPA) | 6 s | ❌ CPML weights | **runs** (via coqui-tts fork venv, verified) |
| YourTTS | short-sample specialist, CPU | 3 s | ✅ | **runs** (via coqui-tts fork venv, verified) |
| OpenVoice v2 | SIM 0.24 (RVCBench, ECAPA) | 3 s | ✅ MIT/MIT | adapter, interface-only runner |
| GPT-SoVITS | few-shot from ~1 min | 5 s | ✅ MIT/MIT | adapter, interface-only runner |
| RVC | pace/emotion preserved by construction (STS) | ~60 s train | ✅ | interface-only (conversion runs in RVC) |
| Piper | — (not a cloner; a CONTROL voice) | — | ✅ | **runs**: synthetic references + DSP base voice |
| DSP ProsodyMatch | **CONTROL — not a voice clone** (prosody-matched baseline) | 2 s | ✅ | **runs**: measured pace/pitch matching |

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
  pace and emotion — and in v0.2 that path is still an interface, not a wrapper.
- **The built-in DSP baseline is a CONTROL, not a clone.** It measurably
  matches pace and pitch; its measured speaker similarity is 0.5447
  (mean, resemblyzer GE2E) against the clones' 0.90+ — the bench report
  shows exactly that, in a separate CONTROLS section, or says
  NOT MEASURED if no embedder is installed.

## Measured proof (v0.2, CPU-only, synthetic speakers)

From `docs/PROOF-2026-11-24.md` (full corpus, committed): 3 lines
(short/neutral, long/formal, emotional) × 2 synthetic Piper speakers
(lessac, female-register; ryan, male-register), every number measured
locally. Similarity = resemblyzer VoiceEncoder (GE2E, 256-dim) cosine vs
the reference; WER = faster-whisper tiny, local.

| Backend | Category | Similarity (mean / range) | WER | Pace |
|---|---|---|---|---|
| XTTS-v2 (neural clone, coqui-tts fork) | CLONE | **0.9187** / 0.8859–0.9359 | 0.00% on 5/6 lines, 15.38% on one | −4.16%…−31.56% |
| YourTTS (neural clone, coqui-tts fork) | CLONE | **0.9032** / 0.8737–0.9211 | 0.00% on all 6 | −9.98%…+18.33% |
| DSP ProsodyMatch | **CONTROL — not a clone** | 0.5447 / 0.4829–0.6052 | 0.00% | within ±0.5% on all 6 |
| Piper base voice | **CONTROL — not a clone** | 0.5713 / 0.5111–0.5984 | 0.00% | — |

Sanity controls, all 6 benches: reference-vs-itself similarity = **1.0**;
different-speaker control = 0.5111–0.5984, clearly below every clone
(min 0.8737). Read the DSP row carefully — that is the harness working as
designed: pace is *measurable and matchable* with no neural model at all
(±0.5%), while similarity exposes the CONTROL as a different speaker.
Nothing estimated, nothing hidden. (v0.1's single-line proof, where
similarity was still NOT MEASURED, is kept at docs/PROOF-2026-11-23.md.)

## CloneForge vs the commercial top

CloneForge is free and local; these are neither. The comparison that
matters is what each side can *prove*:

| | CloneForge (v0.2) | ElevenLabs PVC | HeyGen Voice | Cartesia Sonic | Fish Audio | MiniMax Speech |
|---|---|---|---|---|---|---|
| Price | Free (MIT) | $22/mo Creator | from $29/mo PVC add-on | Pro $5/mo | API $15/1M chars | HD $100/1M chars |
| Runs locally / private | **Yes** | No | No | No (self-host = Enterprise) | Partial (open weights, research licence) | No |
| Published clone accuracy | **Measured on YOUR voice, locally: SIM 0.9032–0.9187 (GE2E) for its two neural runners** | Peer-reviewed best-in-class prosody; no PVC SIM published | AA Controlled-Voice Elo #1 (1,201); no SIM/WER | AA Elo 1,294; no SIM/WER | WER 0.99% EN (vendor report) | SIM 0.738 one-shot EN (paper, earlier model) |
| Measures pace | **Yes — rate diff %, per line** | No published pace metric | No | No | No | No |
| Urdu cloning accuracy | **UNVERIFIED — flagged in the tool** | Listed, unverified | Not in cloning list | Listed as new, unverified | Unverified | Unverified |

The commercial tools are better *cloners* — ElevenLabs' peer-reviewed
prosody evidence is the strongest in the field, and CloneForge's own
router will send a quality-first commercial job there in its reasoning.
What none of them does is run on your machine, for free, and *show you
the measurements on your own reference* — including when the honest
answer is "this CONTROL is not a clone" or "Urdu is UNVERIFIED".

## Licence

MIT for CloneForge's own code. Backends keep their own licences — the
registry and `cloneforge doctor` surface them before you install anything.

## Ethics

Clone only voices you own or have explicit consent to clone. CloneForge's
fixtures are synthetic for a reason.
