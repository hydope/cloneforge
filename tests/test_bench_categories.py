"""Control-vs-clone separation: structural, not cosmetic.

The DSP baseline and the Piper base voice are CONTROLS. If they ever end
up categorised — or reported — as clones, these tests fail.
"""

from cloneforge.bench import (
    CLONE,
    CONTROL,
    BenchReport,
    BenchRow,
    category_for,
    report_markdown,
)


def test_dsp_and_piper_are_controls():
    assert category_for("dsp-prosody") == CONTROL
    assert category_for("piper") == CONTROL


def test_neural_backends_are_clones():
    for backend_id in ("yourtts", "xtts2", "dotstts", "voxcpm2", "f5tts"):
        assert category_for(backend_id) == CLONE


def _report() -> BenchReport:
    return BenchReport(
        line="hello world",
        reference_path="ref.wav",
        reference_duration_s=1.0,
        reference_rate_wpm=120.0,
        reference_f0_hz=180.0,
        rows=[
            BenchRow("yourtts", "YourTTS", "ok", category=CLONE,
                     duration_s=1.1, rate_diff_pct=2.0, similarity=0.81),
            BenchRow("dsp-prosody", "DSP ProsodyMatch", "ok", category=CONTROL,
                     duration_s=1.0, rate_diff_pct=0.1, similarity=0.42),
            BenchRow("dotstts", "dots.tts", "NOT RUN", category=CLONE),
        ],
        embedder_status="resemblyzer VoiceEncoder (GE2E, 256-dim), in-process",
        control_self_similarity=1.0,
        control_different_speaker_similarity=0.42,
    )


def test_report_separates_controls_from_clones():
    md = report_markdown(_report())
    clone_section = md.split("## Voice clones")[1].split("## CONTROLS")[0]
    control_section = md.split("## CONTROLS")[1].split("## Not run")[0]
    assert "YourTTS" in clone_section
    assert "DSP ProsodyMatch" not in clone_section
    assert "DSP ProsodyMatch" in control_section
    assert "not voice clones" in md
    assert "does NOT mean a good clone" in md


def test_report_shows_similarity_controls():
    md = report_markdown(_report())
    assert "reference vs itself = 1.0" in md
    assert "different speaker" in md
