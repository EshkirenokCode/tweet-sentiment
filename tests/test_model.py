import json
from pathlib import Path

import joblib

from tweet_sentiment import LABELS
from tweet_sentiment.evaluate import metrics
from tweet_sentiment.model import build_model


def small_model():
    config = json.loads(Path("configs/experiment.json").read_text())
    config["word_min_df"] = 1
    candidate = config["candidates"][3]
    model = build_model(candidate, config)
    return model.fit(
        [
            "awful bad",
            "terrible bad",
            "meeting today",
            "meeting tomorrow",
            "great good",
            "excellent good",
        ],
        [0, 0, 1, 1, 2, 2],
    )


def test_no_vocabulary_leakage_and_roundtrip(tmp_path):
    model = small_model()
    predictions = model.predict(["validationonlyword good", "testonlyword bad"])
    vocabulary = model.named_steps["tfidf"].vocabulary_
    assert "validationonlyword" not in vocabulary
    assert "testonlyword" not in vocabulary
    joblib.dump(model, tmp_path / "model.joblib")
    restored = joblib.load(tmp_path / "model.joblib")
    assert (restored.predict(["validationonlyword good", "testonlyword bad"]) == predictions).all()


def test_metrics_order_and_mapping():
    assert LABELS == ["negative", "neutral", "positive"]
    result = metrics([0, 1, 2, 2], [0, 2, 1, 2])
    assert result["label_order"] == LABELS
    assert result["confusion_matrix"] == [[1, 0, 0], [0, 0, 1], [0, 1, 1]]
    assert result["per_class"]["positive"]["support"] == 2
    assert result["accuracy"] == 0.5
