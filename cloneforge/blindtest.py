"""Blind listening test — build an A/B pack a human can score honestly.

`cloneforge blindtest` takes pairs of (reference, clone) WAVs that speak
the same line, shuffles which side (A or B) is the clone, and writes:

- `pair-NN-A.wav` / `pair-NN-B.wav` — the shuffled audio,
- `sheet.md` — the scoring sheet a listener fills in (one guess per pair:
  which side is the CLONE?),
- `answer-key.json` — the hidden key. It is written as a separate file
  precisely so it can be kept away from the listener; the sheet never
  contains the answers.

`cloneforge blindtest score <pack-dir>` reads the filled sheet + key and
computes accuracy: fraction correct, per-pair detail. Until a human
fills in a sheet, there is NO result — CloneForge does not score its own
listening test, and the committed example pack states plainly that no
human has scored it yet.
"""

from __future__ import annotations

import json
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

KEY_NAME = "answer-key.json"
SHEET_NAME = "sheet.md"


@dataclass
class Pair:
    pair_id: str
    reference: str
    clone: str
    backend: str = ""


def build_pack(pairs: list[Pair], out_dir: str | Path,
               seed: int | None = None) -> dict:
    """Write a shuffled A/B pack. Returns the answer key dict."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    key: dict[str, dict] = {}
    sheet_pairs = []
    for i, pair in enumerate(pairs, start=1):
        pair_id = f"pair-{i:02d}"
        clone_is_a = rng.random() < 0.5
        a_src, b_src = ((pair.clone, pair.reference) if clone_is_a
                        else (pair.reference, pair.clone))
        a_name = f"{pair_id}-A.wav"
        b_name = f"{pair_id}-B.wav"
        shutil.copyfile(a_src, out / a_name)
        shutil.copyfile(b_src, out / b_name)
        key[pair_id] = {
            "clone_side": "A" if clone_is_a else "B",
            "backend": pair.backend,
            "reference_source": pair.reference,
            "clone_source": pair.clone,
        }
        sheet_pairs.append(pair_id)
    (out / KEY_NAME).write_text(json.dumps(key, indent=2), encoding="utf-8")
    (out / SHEET_NAME).write_text(sheet_markdown(sheet_pairs), encoding="utf-8")
    return key


def sheet_markdown(pair_ids: list[str]) -> str:
    lines = [
        "# Blind listening test — scoring sheet",
        "",
        ("For each pair, listen to A and B (same line, two voices). One is "
         "the real reference recording; the other is a machine clone of it."),
        ("Fill in which side you believe is the **CLONE**: write A or B in "
         "the Guess column. Do not open answer-key.json until you finish."),
        "",
        "| Pair | Guess (A or B) | Confidence (low/med/high) |",
        "|---|---|---|",
    ]
    lines += [f"| {pid} |  |  |" for pid in pair_ids]
    lines += [
        "",
        "When done, score it with: `cloneforge blindtest score <this folder>`",
        "",
    ]
    return "\n".join(lines)


def parse_sheet(path: str | Path) -> dict[str, str]:
    """Parse guesses from a filled sheet: {pair_id: 'A'|'B'}.

    Only table rows whose Guess cell is exactly A or B (any case) count;
    blank guesses are unscored, not wrong.
    """
    guesses: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        pair_id, guess = cells[0], cells[1].upper()
        if pair_id.startswith("pair-") and guess in ("A", "B"):
            guesses[pair_id] = guess
    return guesses


def score_pack(pack_dir: str | Path) -> dict:
    """Unblind and score a filled pack. Accuracy counts answered pairs."""
    pack = Path(pack_dir)
    key = json.loads((pack / KEY_NAME).read_text(encoding="utf-8"))
    guesses = parse_sheet(pack / SHEET_NAME)
    detail = []
    correct = 0
    for pair_id in sorted(key):
        guess = guesses.get(pair_id)
        right = guess is not None and guess == key[pair_id]["clone_side"]
        if right:
            correct += 1
        detail.append({
            "pair": pair_id,
            "backend": key[pair_id].get("backend", ""),
            "clone_side": key[pair_id]["clone_side"],
            "guess": guess,
            "correct": right if guess is not None else None,
        })
    answered = sum(1 for d in detail if d["guess"] is not None)
    return {
        "pairs": len(key),
        "answered": answered,
        "correct": correct,
        "accuracy": (correct / answered) if answered else None,
        "detail": detail,
    }
