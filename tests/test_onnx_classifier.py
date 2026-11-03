from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import numpy as np
import onnxruntime as ort
import pytest

from tweet_sentiment.onnx_classifier import OnnxClassifier


def test_empty_batch_does_not_load_weights():
    classifier = OnnxClassifier(directory="does-not-exist")
    assert classifier.decision_function([]).shape == (0, 3)
    assert classifier.predict([]).shape == (0,)
    assert not hasattr(classifier, "session_")


def test_concurrent_first_use_loads_once():
    classifier = OnnxClassifier()
    with patch("onnxruntime.InferenceSession", wraps=ort.InferenceSession) as factory:
        with ThreadPoolExecutor(max_workers=8) as pool:
            labels = list(pool.map(lambda _: classifier.predict(["A good result."]), range(16)))
        assert factory.call_count == 1
    assert all(np.array_equal(labels[0], row) for row in labels)


def test_failed_initialization_can_retry():
    classifier = OnnxClassifier()
    with patch("tokenizers.Tokenizer.from_file", side_effect=OSError("missing tokenizer")):
        with pytest.raises(OSError, match="missing tokenizer"):
            classifier.predict(["A good result."])
    assert not hasattr(classifier, "session_")
    assert classifier.predict(["A good result."]).shape == (1,)
