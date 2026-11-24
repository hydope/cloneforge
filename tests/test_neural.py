import pytest

from cloneforge.backends import BY_ID
from cloneforge.neural import (
    XTTS_MODEL,
    xtts_available,
    xtts_clone,
    yourtts_available,
    yourtts_clone,
)


def test_availability_check_returns_bool_and_reason():
    ok, reason = yourtts_available()
    assert isinstance(ok, bool)
    assert reason  # always explains itself either way


def test_clone_without_interpreter_raises_honestly(monkeypatch):
    monkeypatch.setattr("cloneforge.neural.tts_interpreter", lambda: None)
    with pytest.raises(RuntimeError, match="unavailable"):
        yourtts_clone("hello", "ref.wav", "out.wav")


def test_xtts_availability_matches_the_shared_fork_probe():
    ok, reason = xtts_available()
    assert isinstance(ok, bool)
    assert reason


def test_xtts_clone_without_interpreter_raises_honestly(monkeypatch):
    monkeypatch.setattr("cloneforge.neural.tts_interpreter", lambda: None)
    with pytest.raises(RuntimeError, match="unavailable"):
        xtts_clone("hello", "ref.wav", "out.wav")


def test_xtts_registry_entry_carries_the_licence_warning():
    xtts = BY_ID["xtts2"]
    assert "xtts_v2" in XTTS_MODEL
    assert xtts.commercial_ok is False
    assert "non-commercial" in xtts.licence_weights
