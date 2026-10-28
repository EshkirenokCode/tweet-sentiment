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
