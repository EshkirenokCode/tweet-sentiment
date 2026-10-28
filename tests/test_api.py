import json
import platform

import joblib
import pytest
from fastapi.testclient import TestClient

from tweet_sentiment import LABELS
from tweet_sentiment.api import create_app
from tweet_sentiment.artifact import versions
from tweet_sentiment.data import sha256

from .test_model import small_model


@pytest.fixture
def artifact(tmp_path):
    joblib.dump(small_model(), tmp_path / "model.joblib")
    metadata = {
        "sha256": sha256(tmp_path / "model.joblib"),
        "dependencies": versions(),
        "python_minor": ".".join(platform.python_version_tuple()[:2]),
        "labels": LABELS,
        "config": {"remove_stopwords": True},
        "model_version": "test",
    }
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))
    return tmp_path


def test_success_and_docs(artifact):
    with TestClient(create_app(artifact)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").json()["status"] == "ready"
        response = client.post("/predict", json={"text": "good great"})
        assert response.status_code == 200
        assert response.json() == {"label": "positive", "model_version": "test"}
        assert client.get("/docs").status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {"text": ""},
        {"text": "  "},
        {"text": 123},
        {"text": None},
        {},
        {"text": "x" * 2001},
        {"text": "..."},
        {"text": "the and"},
        {"text": "good", "extra": True},
    ],
)
def test_invalid_request(artifact, payload):
    with TestClient(create_app(artifact)) as client:
        assert client.post("/predict", json=payload).status_code == 422


def test_body_limit_and_malformed_json(artifact):
    with TestClient(create_app(artifact)) as client:
        assert client.post("/predict", content=b"x" * 8193).status_code == 413
        assert (
            client.post(
                "/predict", content="{broken", headers={"content-type": "application/json"}
            ).status_code
            == 422
        )
        # The middleware counts streamed chunks even without Content-Length.
        request = client.build_request("POST", "/predict", content=iter([b"x" * 5000] * 2))
        assert client.send(request).status_code == 413


@pytest.mark.parametrize("failure", ["missing", "corrupt", "incompatible"])
def test_unavailable_model(artifact, failure):
    if failure == "missing":
        (artifact / "model.joblib").unlink()
    elif failure == "corrupt":
        (artifact / "model.joblib").write_bytes(b"corrupt")
    else:
        path = artifact / "metadata.json"
        metadata = json.loads(path.read_text())
        metadata["dependencies"]["scikit-learn"] = "0.0"
        path.write_text(json.dumps(metadata))
    with TestClient(create_app(artifact)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        assert client.post("/predict", json={"text": "good"}).status_code == 503
