"""CloneForge — a voice-cloning meta-engine, not a new model.

CloneForge does not train or ship a neural voice model. It routes a cloning
job to the best locally installed free backend for the job (by published
benchmark evidence), and — its core differentiator — benchmarks every
installed backend on the *same* line with measured pace, pronunciation and
similarity metrics, marking anything it cannot measure as NOT MEASURED
instead of inventing a number.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
