import pytest

from cloneforge.router import route


def ids(recs):
    return [r.backend.id for r in recs]


def test_accuracy_english_prefers_highest_sim():
    recs, warnings = route(language="en", sample_seconds=30, priority="accuracy")
    assert warnings == []
    top = ids(recs)
    # dots.tts has the highest published SIM; it must outrank OpenVoice (SIM 0.24).
    assert top.index("dotstts") < top.index("openvoice2")


def test_commercial_filter_excludes_noncommercial_weights():
    recs, _ = route(language="en", sample_seconds=30, priority="accuracy",
                    commercial=True)
    chosen = ids(recs)
    assert "f5tts" not in chosen       # CC-BY-NC weights
    assert "xtts2" not in chosen       # CPML weights
    assert "fishs2" not in chosen      # research-only weights
    assert "voxcpm2" in chosen         # Apache code + weights


def test_short_sample_excludes_long_minimum_backends():
    recs, _ = route(language="en", sample_seconds=4, priority="short-sample")
    chosen = ids(recs)
    assert "fishs2" not in chosen      # needs >= 10 s
    assert "rvc" not in chosen         # needs >= 60 s
    assert "yourtts" in chosen or "dsp-prosody" in chosen


def test_pace_priority_puts_voice_conversion_first_and_warns():
    recs, warnings = route(language="en", sample_seconds=600, priority="pace")
    assert recs[0].backend.id == "rvc"
    assert any("invent new timing" in w for w in warnings)


def test_urdu_is_flagged_unverified():
    _recs, warnings = route(language="ur", sample_seconds=30, priority="accuracy")
    assert any("UNVERIFIED" in w and "Urdu" in w for w in warnings)


def test_unknown_priority_rejected():
    with pytest.raises(ValueError):
        route(priority="loudness")


def test_recommendations_carry_reasons():
    recs, _ = route(language="en", sample_seconds=30, priority="accuracy")
    assert recs and all(r.reasons for r in recs)
