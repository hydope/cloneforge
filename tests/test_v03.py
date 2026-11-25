"""v0.3 world-criteria regression tests.

The doctor regression test is the important one: in v0.2, `cloneforge
doctor` reported XTTS/YourTTS "not installed" while the bench ran them,
because doctor probed only the main venv and the bench used the side
venv. Doctor and the bench runner registry must never disagree again.
"""

from unittest import mock

import pytest

from cloneforge import bench, cli
from cloneforge.backends import BY_ID
from cloneforge.dotstts import dotstts_clone, hardware_blocker
from cloneforge.voxcpm import voxcpm_clone


def test_doctor_installed_set_covers_every_executable_runner():
    availability = bench.runner_availability()
    executable = {bid for bid, (ok, _w) in availability.items() if ok}
    doctor_installed = {b.id for b in BY_ID.values() if b.status()[0]}
    missing = executable - doctor_installed
    assert not missing, (
        f"bench can execute {sorted(missing)} but doctor does not "
        "report them INSTALLED — the v0.2 doctor bug is back")


def test_doctor_lines_use_side_venv_status_for_coqui_backends():
    lines = cli.doctor_lines()
    ok, _why = bench.runner_availability()["yourtts"]
    yourtts_line = next(ln for ln in lines if "YourTTS" in ln)
    if ok:
        assert "INSTALLED" in yourtts_line
        assert "side venv" in yourtts_line  # the venv path must be shown
    else:
        assert "not installed" in yourtts_line


def test_bench_rows_carry_latency_and_separate_ecapa_field():
    row = bench.BenchRow("xtts2", "XTTS-v2", "ok", latency_s=85.25,
                         similarity=0.91, similarity_ecapa=0.72)
    assert row.latency_s == 85.25
    # the two scorers are separate fields, never one blended number
    assert row.similarity != row.similarity_ecapa


def test_report_has_separate_similarity_columns_and_latency():
    report = bench.BenchReport(
        line="hello world", reference_path="ref.wav",
        reference_duration_s=1.0, reference_rate_wpm=120.0,
        reference_f0_hz=180.0,
        rows=[bench.BenchRow("yourtts", "YourTTS", "ok", duration_s=1.1,
                             rate_diff_pct=2.0, similarity=0.81,
                             similarity_ecapa=0.66, latency_s=12.5)],
        embedder_status="GE2E method",
        embedder_status_ecapa="ECAPA method",
        control_self_similarity=1.0,
        control_self_similarity_ecapa=1.0,
        control_different_speaker_similarity=0.42,
        control_different_speaker_similarity_ecapa=0.31,
    )
    md = bench.report_markdown(report)
    assert "Similarity GE2E" in md and "Similarity ECAPA" in md
    assert "Latency" in md and "12.50s" in md
    assert "never blended" in md
    assert "controls (ECAPA)" in md


def test_voxcpm_clone_without_interpreter_raises_honestly(monkeypatch):
    monkeypatch.setattr("cloneforge.voxcpm.voxcpm_interpreter", lambda: None)
    with pytest.raises(RuntimeError, match="unavailable"):
        voxcpm_clone("hello", "ref.wav", "out.wav")


def test_dotstts_clone_without_interpreter_states_hardware_blocker(monkeypatch):
    monkeypatch.setattr("cloneforge.dotstts.dotstts_interpreter", lambda: None)
    with pytest.raises(RuntimeError, match="VRAM|RAM"):
        dotstts_clone("hello", "ref.wav", "out.wav")


def test_hardware_blocker_reports_measured_figures():
    blocker = hardware_blocker()
    assert "GB" in blocker  # RAM/VRAM figures, not a vague excuse
    assert "GPU" in blocker


def test_dotstts_runner_with_mocked_backend(tmp_path):
    """The dots.tts runner code path is complete: with a (mocked)
    interpreter whose subprocess 'succeeds', it produces the output."""
    out = tmp_path / "dots.wav"

    def fake_run(cmd, **kwargs):
        out.write_bytes(b"RIFF")
        return mock.Mock(returncode=0, stderr="", stdout="ok")

    with mock.patch("cloneforge.dotstts.dotstts_interpreter",
                    return_value="/fake/python"), \
         mock.patch("cloneforge.dotstts.subprocess.run", side_effect=fake_run):
        result = dotstts_clone("hello", "ref.wav", out)
    assert result["backend"] == "dotstts"
    assert out.exists()


def test_voxcpm_runner_with_mocked_backend(tmp_path):
    out = tmp_path / "vox.wav"

    def fake_run(cmd, **kwargs):
        out.write_bytes(b"RIFF")
        return mock.Mock(returncode=0, stderr="", stdout="ok")

    with mock.patch("cloneforge.voxcpm.voxcpm_interpreter",
                    return_value="/fake/python"), \
         mock.patch("cloneforge.voxcpm.subprocess.run", side_effect=fake_run):
        result = voxcpm_clone("hello", "ref.wav", out, reference_text="hello")
    assert result["backend"] == "voxcpm2"
    assert out.exists()


def test_disable_backends_kill_switch(monkeypatch):
    monkeypatch.setenv("CLONEFORGE_DISABLE_BACKENDS", "voxcpm2,xtts2")
    availability = bench.runner_availability()
    for bid in ("voxcpm2", "xtts2"):
        ok, why = availability[bid]
        assert ok is False
        assert "CLONEFORGE_DISABLE_BACKENDS" in why
    # untouched runners are unaffected
    assert availability["dsp-prosody"][0] is True


def test_ui_function_layer_route_and_synth(tmp_path):
    """Exercise the UI's own functions (not the browser): route + synth."""
    from cloneforge import ui

    text = ui.route_text("en", 10, "accuracy", False)
    assert "VoxCPM2" in text or "dots.tts" in text

    # The synth half needs the Piper voice models, which install.sh
    # downloads (they are not in the repo). Where they are absent
    # (e.g. CI), skip with the reason instead of failing on a missing
    # optional dependency — the full exercise runs wherever the models
    # exist (proof doc, v0.3 round: 55 passed locally).
    import importlib.util
    from pathlib import Path

    import cloneforge
    models = Path(cloneforge.__file__).parent.parent / "models"
    if importlib.util.find_spec("piper") is None or not (
            models / "en_US-lessac-medium.onnx").exists():
        pytest.skip("Piper voice models not installed in this environment")

    from cloneforge.audio import make_reference

    ref = make_reference("The UI synth test reference line.", tmp_path / "ref.wav")
    audio_path, info = ui.synth_dsp("A different line to synthesise.",
                                    str(ref), "The UI synth test reference line.")
    assert audio_path and audio_path.endswith(".wav")
    assert "dsp-prosody" in info
