# Human reference corpus — sources, licences, speakers (all verified)

CloneForge's synthetic Piper fixtures prove the pipeline, but synthetic
voices cannot prove cloning of a *person*. This corpus is the real-human
counterpart. Every fact below was verified in the v0.3 round from the
source named next to it — nothing is assumed.

## Source and licence

- **Dataset:** LibriSpeech ASR corpus, `test-clean` split.
- **Download:** https://www.openslr.org/resources/12/test-clean.tar.gz
  (346,663,984 bytes, downloaded 2026-11-24).
- **Licence: CC BY 4.0** — stated on the dataset's own OpenSLR resource
  page (SLR12, https://www.openslr.org/12, read 2026-11-24: "License:
  CC BY 4.0"). LibriSpeech is derived from LibriVox audiobooks
  (Panayotov et al., ICASSP 2015). Redistribution of these clips in
  this repo is under CC BY 4.0 with this attribution.
- **Why not VCTK / Common Voice for the third speaker:** the v0.3
  checklist named them as examples ("e.g."). VCTK's full archive is
  ~11 GB (over the round's <500 MB download budget) and Common Voice
  downloads require a dataset account/agreement, so neither could be
  fetched and licence-verified inside this round. Three LibriSpeech
  speakers are used instead; the deviation and its reason are recorded
  here rather than papered over.

## Clips (in `examples/corpus/`)

Speaker identity, sex and name are taken from the corpus's own
`SPEAKERS.TXT` (shipped inside the tarball), quoted verbatim.
Durations were measured with ffprobe after conversion to 16 kHz mono
WAV; transcripts are the corpus's own `*.trans.txt` records.

| File | Speaker (SPEAKERS.TXT) | Utterance | Duration | Words |
|---|---|---|---|---|
| `librispeech-1089.wav` | `1089 \| M \| test-clean \| Peter Bobbe` | 1089-134686-0000 | 10.44s | 28 |
| `librispeech-237.wav` | `237 \| F \| test-clean \| rachelellen` | 237-126133-0000 | 13.29s | 38 |
| `librispeech-1221.wav` | `1221 \| F \| test-clean \| Dianne` | 1221-135766-0000 | 12.44s | 37 |

Each clip's transcript is in the sibling `.txt` file (the corpus's
uppercase styling is preserved; CloneForge's WER is case-insensitive).

## Rules for this corpus

- These are real people's voices, published by them for LibriVox and
  redistributed here under CC BY 4.0 for benchmark purposes only.
- Results on human references live in the v0.3 PROOF doc, in tables
  clearly separated from the synthetic-speaker results.
- No other human voice may be added to this repo without its source
  and licence being verified and recorded here first.
