import importlib.metadata
import json
import platform
from pathlib import Path

import joblib

from tweet_sentiment import LABELS
from tweet_sentiment.data import sha256

PACKAGES = ["scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl"]


def versions():
    return {name: importlib.metadata.version(name) for name in PACKAGES}


def load_artifact(directory=Path("artifacts")):
    directory = Path(directory)
    metadata = json.loads((directory / "metadata.json").read_text())
    if metadata["dependencies"] != versions():
        raise ValueError("Artifact dependency versions differ; install requirements.lock")
    if metadata["python_minor"] != ".".join(platform.python_version_tuple()[:2]):
        raise ValueError("Artifact Python version differs")
    if sha256(directory / "model.joblib") != metadata["sha256"]:
        raise ValueError("Artifact checksum mismatch")
    # Only load a repository-owned trusted artifact. The checksum detects corruption, not malice.
    model = joblib.load(directory / "model.joblib")
    if list(model.classes_) != [0, 1, 2] or metadata["labels"] != LABELS:
        raise ValueError("Artifact label mapping mismatch")
    return model, metadata
