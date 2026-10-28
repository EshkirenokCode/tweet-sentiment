import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import joblib
from threadpoolctl import threadpool_limits

from tweet_sentiment import LABELS
from tweet_sentiment.artifact import versions
from tweet_sentiment.data import MANIFEST, sha256, verify, write_json
from tweet_sentiment.evaluate import metrics
from tweet_sentiment.model import build_model


def train(config_path=Path("configs/experiment.json"), artifact_dir=Path("artifacts")):
    if (artifact_dir / "model.joblib").exists():
        raise FileExistsError(
            "Artifact exists. Choose another --artifact-dir for a new experiment."
        )
    splits = verify()
    config = json.loads(config_path.read_text())
    train_x, train_y = splits["train"]
    val_x, val_y = splits["val"]
    results = []
    with threadpool_limits(limits=1):
        for candidate in config["candidates"]:
            model = build_model(candidate, config)
            started = perf_counter()
            model.fit(train_x, train_y)
            elapsed = perf_counter() - started
            result = {
                "config": candidate,
                "train_seconds": elapsed,
                "validation": metrics(val_y, model.predict(val_x)),
            }
            results.append(result)
            print(
                candidate["name"],
                f"F1={result['validation']['macro_f1']:.6f}",
                f"train={elapsed:.2f}s",
                flush=True,
            )
        best = max(results, key=lambda item: item["validation"]["macro_f1"])
        model = build_model(best["config"], config)
        started = perf_counter()
        model.fit(train_x, train_y)
        final_seconds = perf_counter() - started
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_dir / "model.joblib", compress=3)
    metadata = {
        "model_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256(artifact_dir / "model.joblib"),
        "labels": LABELS,
        "config": best["config"],
        "experiment": config,
        "experiment_sha256": sha256(config_path),
        "data_manifest_sha256": sha256(MANIFEST),
        "dependencies": versions(),
        "python_minor": ".".join(platform.python_version_tuple()[:2]),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "training_threads": 1,
        "final_train_seconds": final_seconds,
        "artifact_bytes": (artifact_dir / "model.joblib").stat().st_size,
    }
    write_json(artifact_dir / "metadata.json", metadata)
    write_json(artifact_dir / "config.json", best["config"])
    write_json(artifact_dir / "validation_metrics.json", results)
    print("Selected", best["config"]["name"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/experiment.json"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    train(args.config, args.artifact_dir)
