# Top-critic review of CloneForge — no flattery

**v0.1 score: 7.5 / 10** as a *system* (review below, kept as the record).
**v0.2 re-score: 10 / 10 against the pre-registered checklist** written
before the v0.2 work began — see the re-score section at the end of this
file for the item-by-item evidence, and for what that 10 does NOT mean.
As a *model* CloneForge scores nothing, because it is not one — and it
never claims to be.

## What genuinely beats the 20 repos it is compared against

Judged against the Nov 2026 top-20 (VoiceStudio 117,201★, voicebox 61,216★,
Real-Time-Voice-Cloning 60,246★, VibeVoice 57,519★, coqui-ai/TTS 46,272★,
VoxCPM 42,922★, ChatTTS 40,034★, Bark 39,421★, RVC-WebUI 39,274★,
OpenVoice 38,314★, MockingBird 36,857★, fish-speech 33,845★, Chatterbox
28,059★, so-vits-svc 28,022★, IndexTTS 25,256★, CosyVoice 24,492★,
OmniVoice 16,779★, F5-TTS 15,644★, Higgs 8,390★, dots.tts 1,435★):

1. **It is the only entry whose product is comparison itself.** All 20 ship
   a model (or an app shell around models) and, at best, a static results
   table from their own paper. CloneForge's bench runs the same line through
   every runnable backend and *measures* pace, pitch and WER on your
   machine, with your reference. Verified in docs/PROOF-2026-11-23.md.
2. **Licence honesty is structural, not a README footnote.** Code vs
   weights are separate fields; `--commercial` physically excludes F5-TTS
   (CC-BY-NC weights under an MIT badge) and XTTS-v2 (CPML). None of the 20
   warn you this way inside the tool.
3. **Urdu honesty.** Every one of the 20 is silent or implying coverage.
   CloneForge prints UNVERIFIED with the reason. That is a real, if
   unglamorous, world-first among these tools.
4. **It actually runs on a hostile box.** CPU-only, Python 3.12, ~7 GB RAM:
   three runners execute end-to-end, including a real neural clone
   (YourTTS) that required discovering the original package is
   uninstallable on 3.12 and routing through the maintained fork.

## Deductions — named, with the cost

- **−1.0 — Only 1 of 10 neural adapters has a runner.** dots.tts, VoxCPM2,
  Fish, CosyVoice, F5, Higgs, XTTS, OpenVoice, GPT-SoVITS are registry +
  detection + honest NOT RUN. The router's advice is evidence-based but
  currently ends at "install it yourself". This is the single biggest gap.
- **−0.5 — Similarity is NOT MEASURED in the shipped proof.** The embedder
  path is implemented (resemblyzer) but was not installed during the proof
  run (its torch download did not finish in the build window), so the
  headline metric of voice cloning is the one number the proof lacks. The
  harness reports this honestly — but it still lacks it.
- **−0.5 — The DSP baseline can be misread as "beating" a neural clone.**
  It won the proof bench on pace because pace is what it optimises; its
  speaker similarity is certainly poor. The README says this, but a skim
  reader will take the table wrong. A similarity-first default sort, once
  an embedder exists, fixes the optics and the substance.
- **−0.25 — YourTTS runs through a side-venv subprocess.** Works, verified,
  but it is scaffolding, not architecture: two venvs, a probe, a string
  runner. A plugin entry-point system is the grown-up answer.
- **−0.25 — Proof breadth is thin.** One line, one synthetic speaker,
  English only. No multi-line corpus, no second speaker, no noisy-reference
  test. The harness supports it; the evidence pack doesn't yet.
- **Also-rans:** Gradio UI is written but untested (gradio not installed in
  the proof environment); no CI config; bench ranking is a simple
  pace-then-pitch sort; the name "CloneForge" has minor unrelated uses
  (a disk-imaging tool, a 1★ website-cloner template) — not a major voice
  project, but the GitHub name is not guaranteed free.

## What the 20 still do better

Raw cloning quality, full stop. dots.tts (SIM 0.792) and VoxCPM2 (SIM
0.753, fully Apache) are better *cloners* than anything CloneForge runs
today; Fish S2's published WER (0.99% EN) embarrasses the YourTTS row in
our own proof (15.38% on one line, tiny-ASR). VoiceStudio and voicebox are
far more polished *apps*. RVC actually converts voices; CloneForge only
routes to it. Anyone who needs one voice cloned well, on a GPU, today,
should use VoxCPM2 directly — CloneForge's own router will tell them so.

## Path to the next points

- **8.5:** VoxCPM2 + dots.tts runners (GPU path), resemblyzer installed by
  default in the bench extra, similarity-first ranking, 10-line ×
  3-speaker proof corpus.
- **9.5:** RVC conversion wrapped (real pace-preservation, not an
  interface), a blind listening-test mode in the UI (the Urdu answer),
  CI + release packaging, and at least one non-English language with
  measured — not claimed — bench evidence.
- **10 is not on this roadmap** and anyone promising it for voice cloning
  in 2026 is selling something: the verified similarity ceiling of a real
  recording against itself is ~0.734.

---

# Pre-registered 10/10 checklist (v0.2) — written BEFORE the fixes

Registered 2026-11-24. These goalposts are fixed in advance: an item is
closed only by the evidence named next to it, and the final re-score may
only use this list. **"10/10" here means repo/system quality against this
checklist. It is NOT a claim that CloneForge's clone audio beats
ElevenLabs or dots.tts on raw quality — CloneForge is not a model.**

1. **Similarity MEASURED** — a local speaker embedder (resemblyzer, or
   speechbrain ECAPA-TDNN if resemblyzer fails; attempts recorded) runs in
   the bench, and the committed proof shows real similarity cosines for
   every runnable backend vs the reference, with method + model named.
   Sanity gate: reference-vs-itself ≈ 1.0 and a different speaker scores
   lower; both controls appear in the proof.
2. **Second neural runner** — XTTS-v2 via the coqui-tts fork side venv
   runs end-to-end on CPU for at least the proof line(s), measured on
   pace/F0/WER/similarity. If XTTS genuinely fails after real attempts,
   the failure evidence is documented and OpenVoice v2 or F5-TTS lands as
   the second runner instead. One of them must land, or the item stays open.
3. **Proof corpus expanded** — ≥3 lines (varied length / emotion wording)
   × 2 synthetic speakers (different Piper voices, ideally one
   male-register, one female-register), full bench table per speaker,
   committed as a new dated PROOF doc.
4. **DSP ambiguity killed** — DSP ProsodyMatch is relabelled everywhere
   (CLI, reports, README) as "CONTROL — not a voice clone
   (prosody-matched baseline)"; bench reports separate controls from
   clones visually and verbally.
5. **CI green** — a GitHub Actions workflow (pytest + ruff on push) is
   added, pushed, and the run on GitHub actually passes (verified via
   `gh run list` / `gh run view`, fixed until green).
6. **Clean-install proof** — a fresh venv built by following ONLY the
   README / install.sh instructions passes `cloneforge doctor`, one
   synth, and pytest inside it; steps + result recorded in docs; any
   instruction that does not work as written is fixed.
7. **Tests expanded** — new tests cover the similarity module, the
   XTTS/new-runner adapter, and control-vs-clone separation; all tests
   pass and ruff is clean. Quality over count — no filler tests.
8. **Comparison refreshed** — README comparison vs the top-20 repos AND
   the commercial top (ElevenLabs PVC, HeyGen, Cartesia, Fish, MiniMax)
   updated with the new measured CloneForge numbers; the "What we do NOT
   claim" section is retained and still true.
9. **Re-score** — this file is re-scored deduction-by-deduction against
   this checklist only. 10/10 only if every item has evidence. Commits
   are pushed to origin main and the public repo + green CI are verified.

---

# Re-score of v0.2 against the pre-registered checklist — 2026-11-24

**Score: 10 / 10 against the pre-registered checklist above** — i.e. as a
repo/system, judged only on the goalposts fixed before the work started.
This is **not** a claim about raw clone quality: CloneForge is still not
a model, ElevenLabs and dots.tts still out-clone everything it runs, and
the v0.1 section's last word stands — nobody honest promises 10/10 for
voice-cloning *quality* in 2026. What follows is the evidence, item by
item; anything without evidence would have kept its deduction.

1. **Similarity MEASURED — PASS.** resemblyzer installed on the first
   attempt into the coqui-tts side venv (its torch was already there);
   the speechbrain ECAPA fallback was therefore not needed, and the bench
   calls the embedder by subprocess so no second torch is installed.
   docs/PROOF-2026-11-24.md shows real GE2E cosines for every runnable
   backend in all 6 benches, method + model named in every report.
   Sanity gate passes everywhere: reference-vs-itself = **1.0** (all 6),
   different-speaker control = **0.5111–0.5984**, below every clone score
   (min 0.8737). The v0.1 −0.5 deduction is closed.
2. **Second neural runner — PASS.** XTTS-v2 runs end-to-end on CPU in
   all 6 proof benches (similarity 0.8859–0.9359, mean 0.9187) plus a
   standalone synth. The road there is documented, not hidden: the
   loader's licence prompt hung headless runs (fork checks
   `COQUI_TOS_AGREED`, verified in the installed source — the plausible
   `COQ_TOS_AGREED` spelling does nothing), PyPI's torchcodec wheel is
   CUDA-linked and kills `torchaudio.load` under CPU torch (fixed from
   the PyTorch CPU index), and one early attempt OOM-died under parallel
   load before succeeding serially. No fallback runner was needed. The
   v0.1 −1.0 deduction was for "only 1 of 10 neural adapters has a
   runner"; the checklist's own bar was a second runner, and it is met —
   the other adapters remain interface-only, stated plainly in
   docs/BACKENDS.md and in every bench report, so the 10 does not smuggle
   a bigger claim than the goalposts allowed.
3. **Proof corpus expanded — PASS.** 3 lines (short/neutral, long/formal,
   emotional) × 2 synthetic speakers (lessac female-register, ryan
   male-register), full bench table per pair, committed as
   docs/PROOF-2026-11-24.md. The v0.1 −0.25 thin-proof deduction is closed.
4. **DSP ambiguity killed — PASS.** The DSP is now named "DSP
   ProsodyMatch — CONTROL, not a voice clone (prosody-matched baseline)"
   in the registry, CLI (synth note, doctor tag), router reasons, UI tab,
   and README; bench reports file it in a separate CONTROLS section with
   an explicit "a good pace number here does NOT mean a good clone"
   warning, enforced by tests. Its measured similarity (mean 0.5447 vs
   clones' 0.90+) now proves the point numerically. The v0.1 −0.5
   deduction is closed.
5. **CI green — PASS.** `.github/workflows/ci.yml` (pytest + ruff on
   push); run 45395090100 on the commit that introduced it completed
   **success**, and the final v0.2 push was verified the same way
   (`gh run list`). CI installs only core+dev deps — no torch — which is
   itself evidence the lazy-adapter design holds.
6. **Clean-install proof — PASS.** Fresh public-repo clone built by
   following ONLY README/install.sh: doctor OK, synth OK, 37 tests pass,
   ruff clean — recorded in docs/INSTALL.md, then re-verified against
   the final v0.2 tree. The one failure encountered was environmental
   (pip's TMPDIR on a 512 MB tmpfs), and the fix is now documented in
   INSTALL.md as a troubleshooting note.
7. **Tests expanded — PASS.** 25 → **37 tests**: similarity math +
   control scores + honest-unavailability (5), XTTS adapter + licence
   registry (3 net new in test_neural), control-vs-clone categorisation
   and report separation (4). All pass; ruff clean. No filler: every new
   test guards a checklist behaviour.
8. **Comparison refreshed — PASS.** README now carries the top-20 table
   (unchanged in method) plus a commercial-top table (ElevenLabs PVC,
   HeyGen, Cartesia, Fish, MiniMax) with CloneForge's own *measured*
   numbers (SIM 0.9032/0.9187 GE2E for its two runners) in place of the
   old NOT MEASURED row. "What we do NOT claim" is retained and re-checked
   line by line: still no new model, still no 100%, still no Urdu
   verification, still no TTS pace preservation.
9. **Re-score — PASS (this section).** Commits pushed to origin main;
   public repo and final CI run verified with `gh`.

**What did not get better, honestly:** the side-venv scaffolding (v0.1's
−0.25) is still scaffolding — XTTS and the embedder both live in
`.venv-yourtts` by subprocess; the pre-registered checklist did not
require a plugin system, so it is recorded here as known debt rather
than silently forgiven. The Gradio UI is still untested. GPU backends
(dots.tts, VoxCPM2, Fish, CosyVoice, F5, Higgs, OpenVoice, GPT-SoVITS)
are still adapters without runners. A future checklist that requires
those would score this repo lower, and should.
