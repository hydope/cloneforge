from cloneforge import cli
from cloneforge.backends import BACKENDS, BY_ID


def test_registry_ids_unique():
    all_ids = [b.id for b in BACKENDS]
    assert len(all_ids) == len(set(all_ids))


def test_licence_split_is_recorded():
    f5 = BY_ID["f5tts"]
    assert f5.licence_code == "MIT"
    assert "CC-BY-NC" in f5.licence_weights
    assert f5.commercial_ok is False
    vox = BY_ID["voxcpm2"]
    assert vox.commercial_ok is True


def test_published_figures_have_benchmark_names():
    for b in BACKENDS:
        if b.sim_en is not None:
            assert b.sim_benchmark, f"{b.id} has a SIM with no benchmark named"
        if b.wer_en is not None:
            assert b.wer_benchmark, f"{b.id} has a WER with no benchmark named"


def test_dsp_baseline_always_installed():
    assert BY_ID["dsp-prosody"].installed() is True


def test_cli_backends_smoke(capsys):
    assert cli.main(["backends"]) == 0
    out = capsys.readouterr().out
    assert "voxcpm2" in out and "dotstts" in out


def test_cli_route_smoke(capsys):
    assert cli.main(["route", "--lang", "ur", "--sample", "30"]) == 0
    out = capsys.readouterr().out
    assert "UNVERIFIED" in out


def test_cli_doctor_smoke(capsys):
    assert cli.main(["doctor"]) == 0
    assert "CloneForge" in capsys.readouterr().out
