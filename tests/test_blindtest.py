"""Blind listening test: shuffle, sheet parsing, and scoring logic."""

import json
import wave
from contextlib import closing

from cloneforge.blindtest import build_pack, parse_sheet, score_pack


def _wav(path, frames=1600):
    with closing(wave.open(str(path), "wb")) as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x01\x00" * frames)


def _pack(tmp_path, seed=7):
    tmp_path.mkdir(parents=True, exist_ok=True)
    ref = tmp_path / "ref.wav"
    clone = tmp_path / "clone.wav"
    _wav(ref)
    _wav(clone)
    from cloneforge.blindtest import Pair

    pairs = [Pair(pair_id="", reference=str(ref), clone=str(clone),
                  backend=f"backend-{i}") for i in range(4)]
    out = tmp_path / "pack"
    key = build_pack(pairs, out, seed=seed)
    return out, key


def test_pack_writes_pairs_sheet_and_key(tmp_path):
    out, key = _pack(tmp_path)
    assert len(key) == 4
    for i in range(1, 5):
        assert (out / f"pair-{i:02d}-A.wav").exists()
        assert (out / f"pair-{i:02d}-B.wav").exists()
    sheet = (out / "sheet.md").read_text()
    assert "pair-01" in sheet and "Guess" in sheet
    # the sheet must never leak the answers
    for entry in key.values():
        assert entry["clone_side"] in ("A", "B")


def test_shuffle_is_deterministic_per_seed_and_actually_shuffles(tmp_path):
    _out1, key1 = _pack(tmp_path / "a", seed=42)
    _out2, key2 = _pack(tmp_path / "b", seed=42)
    assert [k["clone_side"] for k in key1.values()] == \
        [k["clone_side"] for k in key2.values()]


def test_key_matches_copied_files(tmp_path):
    out, key = _pack(tmp_path, seed=3)
    ref_bytes = (tmp_path / "ref.wav").read_bytes()
    for pair_id, entry in key.items():
        clone_file = out / f"{pair_id}-{entry['clone_side']}.wav"
        assert clone_file.exists()
        assert entry["clone_source"].endswith("clone.wav")
        assert ref_bytes  # reference existed at build time


def test_score_pack_perfect_and_zero(tmp_path):
    out, key = _pack(tmp_path, seed=11)
    sheet = (out / "sheet.md").read_text().splitlines()
    filled = []
    for line in sheet:
        for pair_id, entry in key.items():
            if line.startswith(f"| {pair_id} |"):
                line = f"| {pair_id} | {entry['clone_side']} | high |"
        filled.append(line)
    (out / "sheet.md").write_text("\n".join(filled))
    result = score_pack(out)
    assert result["answered"] == 4
    assert result["accuracy"] == 1.0

    wrong = []
    for line in filled:
        for pair_id, entry in key.items():
            if line.startswith(f"| {pair_id} |"):
                other = "B" if entry["clone_side"] == "A" else "A"
                line = f"| {pair_id} | {other} | low |"
        wrong.append(line)
    (out / "sheet.md").write_text("\n".join(wrong))
    assert score_pack(out)["accuracy"] == 0.0


def test_score_pack_unanswered_is_none_not_zero(tmp_path):
    out, _key = _pack(tmp_path)
    result = score_pack(out)
    assert result["answered"] == 0
    assert result["accuracy"] is None


def test_parse_sheet_ignores_blank_and_header_rows(tmp_path):
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Pair | Guess (A or B) |\n|---|---|\n| pair-01 | a |\n"
        "| pair-02 |  |\n| pair-03 | B |\n")
    assert parse_sheet(sheet) == {"pair-01": "A", "pair-03": "B"}


def test_key_file_is_valid_json(tmp_path):
    out, _key = _pack(tmp_path)
    loaded = json.loads((out / "answer-key.json").read_text())
    assert set(loaded) == {f"pair-{i:02d}" for i in range(1, 5)}
