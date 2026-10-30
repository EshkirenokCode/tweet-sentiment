from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tweet_sentiment import LABELS
from tweet_sentiment.api import create_app
from tweet_sentiment.artifact import load_artifact


@pytest.mark.integration
def test_real_artifact():
    if not Path("artifacts/model.joblib").exists():
        pytest.fail("Real artifact must be present for integration tests")
    model, metadata = load_artifact()
    examples = [
        "The update works really well.",
        "I cannot use the app. It keeps crashing!",
        "The next meeting starts at ten.",
        "Not bad at all!",
        "🙂",
        "@user",
    ]
    expected = model.predict(examples)
    with TestClient(create_app()) as client:
        assert client.get("/ready").status_code == 200
        for text, label in zip(examples, expected, strict=True):
            response = client.post("/predict", json={"text": text})
            assert response.status_code == 200
            assert response.json() == {
                "label": LABELS[label],
                "model_version": metadata["model_version"],
            }


@pytest.mark.integration
def test_loaded_pipeline_roundtrip(tmp_path):
    import joblib
    import numpy as np

    model, _ = load_artifact()
    examples = ["I cannot recommend this.", "The meeting starts at ten.", "Wonderful news!"]
    expected = model.predict(examples)
    joblib.dump(model, tmp_path / "model.joblib")
    restored = joblib.load(tmp_path / "model.joblib")
    assert np.array_equal(restored.predict(examples), expected)


@pytest.mark.integration
def test_encoder_token_limit():
    model, metadata = load_artifact()
    if not metadata.get("assets"):
        pytest.skip("Sparse model has no encoder token limit")
    with TestClient(create_app()) as client:
        response = client.post("/predict", json={"text": "xy! " * 100})
        assert response.status_code == 422
        assert "256 tokens" in response.json()["detail"]


@pytest.mark.integration
def test_corrupt_encoder_is_not_ready(tmp_path):
    import json
    import shutil

    shutil.copyfile("artifacts/model.joblib", tmp_path / "model.joblib")
    metadata = json.loads(Path("artifacts/metadata.json").read_text())
    if not metadata.get("assets"):
        pytest.skip("Sparse model has no encoder assets")
    metadata["assets"] = {"encoder/model.onnx": metadata["assets"]["encoder/model.onnx"]}
    (tmp_path / "encoder").mkdir()
    (tmp_path / "encoder/model.onnx").write_bytes(b"corrupt")
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
