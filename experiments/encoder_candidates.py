import json
import shutil
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
from huggingface_hub import hf_hub_download
from scipy.sparse import csr_matrix, hstack
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from tweet_sentiment.data import verify, write_json
from tweet_sentiment.encoder import OnnxEncoder
from tweet_sentiment.evaluate import metrics
from tweet_sentiment.model import build_model
from tweet_sentiment.preprocessing import TextNormalizer

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
OUTPUT = Path("experiments/v1.2-encoder")


def run():
    OUTPUT.mkdir(exist_ok=True)
    for remote, local in [
        ("onnx/model_qint8_arm64.onnx", "model.onnx"),
        ("tokenizer.json", "tokenizer.json"),
    ]:
        shutil.copyfile(hf_hub_download(MODEL, remote, revision=REVISION), OUTPUT / local)
    splits = verify()
    encoder = OnnxEncoder(str(OUTPUT), batch_size=64, threads=4)
    normalizer = TextNormalizer(False, version=2)
    vectors = {}
    for split in ("train", "val"):
        path = OUTPUT / f"{split}.npy"
        if path.exists():
            vectors[split] = np.load(path)
            continue
        texts = normalizer.transform(splits[split][0])
        start = perf_counter()
        parts = []
        for index in range(0, len(texts), 1024):
            parts.append(encoder.transform(texts[index : index + 1024]))
            print(
                "Encoded",
                split,
                min(index + 1024, len(texts)),
                len(texts),
                f"{perf_counter() - start:.1f}s",
                flush=True,
            )
        vectors[split] = np.concatenate(parts)
        np.save(path, vectors[split])
    config = json.loads(Path("configs/experiment.json").read_text())
    config["word_max_features"] = config["char_max_features"] = 150000
    feature_pipeline = build_model(
        {"kind": "svc", "char": True, "remove_stopwords": False, "C": 0.1}, config
    )[:-1]
    word_train = feature_pipeline.fit_transform(*splits["train"])
    word_val = feature_pipeline.transform(splits["val"][0])
    rows = []
    with threadpool_limits(1):
        candidates = [("embeddings", c, None) for c in (1, 10, 100)] + [
            ("hybrid", 0.1, None),
            ("hybrid", 1, None),
            ("hybrid", 0.1, "balanced"),
        ]
        for family, c, weight in candidates:
            if family == "embeddings":
                train, val = vectors["train"], vectors["val"]
                classifier = LogisticRegression(C=c, max_iter=1000, random_state=42)
            else:
                train = hstack([word_train, csr_matrix(vectors["train"])], format="csr")
                val = hstack([word_val, csr_matrix(vectors["val"])], format="csr")
                classifier = LinearSVC(
                    C=c, class_weight=weight, dual=True, max_iter=5000, random_state=42
                )
            start = perf_counter()
            classifier.fit(train, splits["train"][1])
            row = {
                "family": family,
                "C": c,
                "class_weight": weight,
                "fit_seconds": perf_counter() - start,
                "validation": metrics(splits["val"][1], classifier.predict(val)),
            }
            rows.append(row)
            write_json(OUTPUT / "validation.json", rows)
            print(row, flush=True)
            if row is max(rows, key=lambda item: item["validation"]["macro_f1"]):
                joblib.dump(classifier, OUTPUT / "classifier.joblib", compress=3)
                joblib.dump(feature_pipeline, OUTPUT / "sparse_features.joblib", compress=3)
                write_json(OUTPUT / "best.json", row)


if __name__ == "__main__":
    run()
