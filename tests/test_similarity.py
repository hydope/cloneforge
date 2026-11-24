"""Similarity module: the math and the controls, without needing torch.

The embedder itself is exercised in the committed bench proof; here we
test the parts that must never lie: cosine use, control-score plumbing,
and honest unavailability.
"""

import pytest

from cloneforge import similarity
from cloneforge.metrics import cosine_similarity


class FakeEmbedder:
    """Deterministic stand-in: maps file names to fixed embeddings."""

    method = "fake embedder (test)"
    mode = "fake"

    def __init__(self, table):
        self.table = table

    def embed_many(self, paths):
        return [self.table[p] for p in paths]

    def embed(self, path):
        return self.table[path]


def test_similarity_of_identical_vectors_is_one():
    emb = FakeEmbedder({"a.wav": [1.0, 2.0, 3.0], "b.wav": [1.0, 2.0, 3.0]})
    assert similarity.similarity(emb, "a.wav", "b.wav") == pytest.approx(1.0)


def test_similarity_of_orthogonal_vectors_is_zero():
    emb = FakeEmbedder({"a.wav": [1.0, 0.0], "b.wav": [0.0, 1.0]})
    assert similarity.similarity(emb, "a.wav", "b.wav") == pytest.approx(0.0)


def test_control_scores_self_is_one_and_other_is_lower():
    emb = FakeEmbedder({
        "ref.wav": [1.0, 0.2, 0.1],
        "other.wav": [0.1, 1.0, 0.2],
    })
    scores = similarity.control_scores(emb, "ref.wav", "other.wav")
    assert scores["self"] == pytest.approx(1.0)
    assert scores["different_speaker"] < scores["self"]
    assert scores["different_speaker"] == pytest.approx(
        cosine_similarity([1.0, 0.2, 0.1], [0.1, 1.0, 0.2]))


def test_embedder_status_always_explains_itself():
    ok, reason = similarity.embedder_status()
    assert isinstance(ok, bool)
    assert reason  # a status with no method named is not a measurement


def test_get_embedder_returns_none_or_typed_embedder():
    emb = similarity.get_embedder()
    assert emb is None or isinstance(emb, similarity.Embedder)
    if emb is not None:
        assert "resemblyzer" in emb.method  # the method must be named
