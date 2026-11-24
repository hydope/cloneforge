import math

import pytest

from cloneforge.metrics import (
    cosine_similarity,
    duration_ratio,
    median_f0_hz,
    rate_difference_pct,
    speech_rate_wpm,
    wer,
)


def test_wer_identical_is_zero():
    assert wer("the quick brown fox", "The quick brown fox!") == 0.0


def test_wer_one_substitution_of_four():
    assert wer("the quick brown fox", "the quick red fox") == 25.0


def test_wer_insertion_and_deletion():
    assert wer("hello world", "hello") == 50.0
    assert wer("hello world", "hello brave world") == 50.0


def test_wer_empty_reference_raises():
    with pytest.raises(ValueError):
        wer("", "anything")


def test_duration_ratio():
    assert duration_ratio(2.0, 2.0) == 1.0
    assert duration_ratio(2.0, 3.0) == 1.5
    with pytest.raises(ValueError):
        duration_ratio(0.0, 1.0)


def test_speech_rate_and_difference():
    assert speech_rate_wpm(30, 15.0) == 120.0
    assert rate_difference_pct(120.0, 132.0) == pytest.approx(10.0)
    assert rate_difference_pct(120.0, 120.0) == 0.0


def test_cosine_similarity():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0, 1.0], [-1.0, -1.0]) == pytest.approx(-1.0)
    with pytest.raises(ValueError):
        cosine_similarity([1.0], [1.0, 2.0])


def test_median_f0_finds_sine_pitch():
    pytest.importorskip("numpy")
    import numpy as np

    sr = 16000
    t = np.arange(sr) / sr
    sine = (0.5 * np.sin(2 * math.pi * 120.0 * t)).tolist()
    f0 = median_f0_hz(sine, sr)
    assert f0 is not None
    assert 110.0 < f0 < 130.0


def test_median_f0_silence_is_none_not_zero():
    pytest.importorskip("numpy")
    assert median_f0_hz([0.0] * 16000, 16000) is None
