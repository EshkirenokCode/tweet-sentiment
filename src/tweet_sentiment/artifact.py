import importlib.metadata
import json
import platform
from pathlib import Path

import joblib

from tweet_sentiment import LABELS
from tweet_sentiment.data import sha256

PACKAGES = ["scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl"]


def versions(names=PACKAGES):
    return {name: importlib.metadata.version(name) for name in names}


def load_artifact(directory=Path("artifacts")):
    directory = Path(directory)
    metadata = json.loads((directory / "metadata.json").read_text())
    if not set(PACKAGES) <= metadata["dependencies"].keys():
        raise ValueError("Artifact dependency metadata is incomplete")
    if metadata["dependencies"] != versions(metadata["dependencies"]):
        raise ValueError("Artifact dependency versions differ; install requirements.lock")
    if metadata["python_minor"] != ".".join(platform.python_version_tuple()[:2]):
        raise ValueError("Artifact Python version differs")
    if sha256(directory / "model.joblib") != metadata["sha256"]:
        raise ValueError("Artifact checksum mismatch")
    for name, checksum in metadata.get("assets", {}).items():
        if sha256(directory / name) != checksum:
            raise ValueError(f"Artifact asset checksum mismatch: {name}")
    # Only load a repository-owned trusted artifact. The checksum detects corruption, not malice.
    model = joblib.load(directory / "model.joblib")
    if list(model.classes_) != [0, 1, 2] or metadata["labels"] != LABELS:
        raise ValueError("Artifact label mapping mismatch")
    if metadata.get("assets"):
        model.named_steps["classifier"].set_params(directory=str(directory / "encoder"))
        model.predict(["The service is ready."])
    return model, metadata
