from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class TokenLimitError(ValueError):
    pass


class OnnxEncoder(TransformerMixin, BaseEstimator):
    def __init__(self, directory="artifacts/encoder", batch_size=64, threads=1, max_tokens=256):
        self.directory = directory
        self.batch_size = batch_size
        self.threads = threads
        self.max_tokens = max_tokens

    def fit(self, X, y=None):
        return self

    def __getstate__(self):
        return {
            key: value
            for key, value in self.__dict__.items()
            if key not in ("session_", "tokenizer_")
        }

    def _load(self):
        if hasattr(self, "session_"):
            return
        import onnxruntime as ort
        from tokenizers import Tokenizer

        options = ort.SessionOptions()
        options.intra_op_num_threads = self.threads
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        path = Path(self.directory)
        self.session_ = ort.InferenceSession(
            str(path / "model.onnx"), options, providers=["CPUExecutionProvider"]
        )
        self.tokenizer_ = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tokenizer_.no_truncation()
        self.tokenizer_.enable_padding(pad_id=0, pad_token="[PAD]")

    def transform(self, X):
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
            inputs = {
                key: value
                for key, value in inputs.items()
                if key in {item.name for item in self.session_.get_inputs()}
            }
            hidden = self.session_.run(None, inputs)[0]
            mask = inputs["attention_mask"][..., None]
            pooled = (hidden * mask).sum(axis=1) / mask.sum(axis=1).clip(min=1)
            pooled /= np.linalg.norm(pooled, axis=1, keepdims=True).clip(min=1e-12)
            rows.append(pooled.astype(np.float32))
        return np.concatenate(rows)
