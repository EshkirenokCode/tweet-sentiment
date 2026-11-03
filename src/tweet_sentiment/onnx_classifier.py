import threading
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

from tweet_sentiment.encoder import TokenLimitError

_LOAD_LOCK = threading.Lock()


class OnnxClassifier(ClassifierMixin, BaseEstimator):
    def __init__(self, directory="artifacts/encoder", batch_size=1, threads=1, max_tokens=256):
        self.directory = directory
        self.batch_size = batch_size
        self.threads = threads
        self.max_tokens = max_tokens
        self.classes_ = np.arange(3)

    def __getstate__(self):
        return {
            key: value
            for key, value in self.__dict__.items()
            if key not in ("session_", "tokenizer_", "lock_")
        }

    def _load(self):
        if hasattr(self, "session_"):
            return
        with _LOAD_LOCK:
            if not hasattr(self, "session_"):
                self._initialize()

    def _initialize(self):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        options = ort.SessionOptions()
        options.intra_op_num_threads = self.threads
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        path = Path(self.directory)
        session = ort.InferenceSession(
            str(path / "model.onnx"), options, providers=["CPUExecutionProvider"]
        )
        tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        tokenizer.no_truncation()
        tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        self.tokenizer_ = tokenizer
        self.lock_ = threading.Lock()
        self.session_ = session

    def fit(self, X, y=None):
        raise RuntimeError("Fine-tune weights with experiments/finetune_minilm.py")

    def decision_function(self, X):
        if len(X) == 0:
            return np.empty((0, 3), dtype=np.float32)
        self._load()
        rows = []
        for start in range(0, len(X), self.batch_size):
            encoded = self.tokenizer_.encode_batch(list(X[start : start + self.batch_size]))
            if any(len(row.ids) > self.max_tokens for row in encoded):
                raise TokenLimitError(f"Text exceeds the encoder limit of {self.max_tokens} tokens")
            inputs = {
                "input_ids": np.array([row.ids for row in encoded], dtype=np.int64),
                "attention_mask": np.array([row.attention_mask for row in encoded], dtype=np.int64),
                "token_type_ids": np.array([row.type_ids for row in encoded], dtype=np.int64),
            }
            with self.lock_:
                rows.append(self.session_.run(None, inputs)[0])
        return np.concatenate(rows)

    def predict(self, X):
        return self.classes_[self.decision_function(X).argmax(axis=1)]
