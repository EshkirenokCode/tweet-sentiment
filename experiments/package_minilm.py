import argparse
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from tweet_sentiment import LABELS, __version__
from tweet_sentiment.artifact import versions
from tweet_sentiment.data import sha256, write_json
from tweet_sentiment.onnx_classifier import OnnxClassifier
from tweet_sentiment.preprocessing import TextNormalizer


def package(output):
    if output.exists():
        raise FileExistsError(output)
    source = Path("experiments/v1.2-finetuned")
    selection = json.loads((source / "selection.json").read_text())
    training = json.loads((source / "training.json").read_text())
    (output / "encoder").mkdir(parents=True)
    shutil.copyfile(source / f"{selection['precision']}.onnx", output / "encoder/model.onnx")
    shutil.copyfile(source / "checkpoint/tokenizer.json", output / "encoder/tokenizer.json")
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(Path("artifacts/encoder") / name, output / "encoder" / name)
    model = Pipeline(
        [("normalize", TextNormalizer(False, version=2)), ("classifier", OnnxClassifier())]
    )
    joblib.dump(model, output / "model.joblib", compress=3)
    config = {
        "name": "minilm_finetuned_" + selection["precision"],
        "kind": "onnx_minilm",
        "remove_stopwords": False,
        "char": False,
        "preprocessing_version": 2,
        "max_tokens": 256,
    }
    assets = {
        name: sha256(output / name) for name in ["encoder/model.onnx", "encoder/tokenizer.json"]
    }
    metadata = {
        "model_version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256(output / "model.joblib"),
        "labels": LABELS,
        "config": config,
        "assets": assets,
        "experiment": training,
        "experiment_sha256": sha256("experiments/protocol-v1.2.md"),
        "data_manifest_sha256": sha256("reports/data_manifest.json"),
        "dependencies": versions(
            [
                "scikit-learn",
                "numpy",
                "scipy",
                "joblib",
                "threadpoolctl",
                "onnxruntime",
                "tokenizers",
            ]
        ),
        "python_minor": ".".join(platform.python_version_tuple()[:2]),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "training_threads": 4,
        "final_train_seconds": training["seconds"],
        "artifact_bytes": (output / "model.joblib").stat().st_size
        + sum((output / name).stat().st_size for name in assets),
        "source": {
            "name": training["source"],
            "revision": training["revision"],
            "license": "Apache-2.0",
        },
        "selection": selection,
        "test_status": "Previously inspected; repeat measurement.",
    }
    write_json(output / "metadata.json", metadata)
    write_json(output / "config.json", config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/reproduced"))
    package(parser.parse_args().output)
