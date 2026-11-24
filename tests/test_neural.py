import pytest

from cloneforge.neural import yourtts_available, yourtts_clone


def test_availability_check_returns_bool_and_reason():
    ok, reason = yourtts_available()
    assert isinstance(ok, bool)
    assert reason  # always explains itself either way


def test_clone_without_interpreter_raises_honestly(monkeypatch):
    monkeypatch.setattr("cloneforge.neural.tts_interpreter", lambda: None)
    with pytest.raises(RuntimeError, match="unavailable"):
        yourtts_clone("hello", "ref.wav", "out.wav")
