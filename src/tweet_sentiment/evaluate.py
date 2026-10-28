import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from tweet_sentiment import LABELS
from tweet_sentiment.data import MANIFEST, sha256, verify, write_json
from tweet_sentiment.preprocessing import normalize


def metrics(y, predictions):
    report = classification_report(
        y, predictions, labels=[0, 1, 2], target_names=LABELS, output_dict=True, zero_division=0
    )
    return {
        "count": len(y),
        "label_order": LABELS,
        "accuracy": accuracy_score(y, predictions),
        "macro_precision": report["macro avg"]["precision"],
        "macro_recall": report["macro avg"]["recall"],
        "macro_f1": report["macro avg"]["f1-score"],
        "per_class": {label: report[label] for label in LABELS},
        "confusion_matrix": confusion_matrix(y, predictions, labels=[0, 1, 2]).tolist(),
    }


def evaluate(artifact_dir=Path("artifacts"), output=Path("reports/test_metrics.json")):
    from tweet_sentiment.artifact import load_artifact

    if output.exists():
        raise FileExistsError(
            "Test already evaluated. Use a different --output for an explicit rerun."
        )
    model, metadata = load_artifact(artifact_dir)
    if sha256(MANIFEST) != metadata["data_manifest_sha256"]:
        raise ValueError("Data manifest does not match model")
    splits = verify()
    texts, y = splits["test"]
    predictions = model.predict(texts)
    seen = {normalize(x) for s in ("train", "val") for x in splits[s][0]}
    clean = [i for i, text in enumerate(texts) if normalize(text) not in seen]
    result = {
        "model_version": metadata["model_version"],
        "artifact_sha256": metadata["sha256"],
        "data_manifest_sha256": metadata["data_manifest_sha256"],
        "official": metrics(y, predictions),
        "unseen_normalized": metrics(np.array(y)[clean], predictions[clean]),
        "excluded_overlap_rows": len(y) - len(clean),
        "empty_policy": "Official metrics include every row; API rejects empty normalized inputs.",
    }
    write_json(output, result)
    write_json(
        output.with_name(output.stem + "_predictions.json"),
        [
            {"test_index": i, "gold": int(gold), "predicted": int(pred)}
            for i, (gold, pred) in enumerate(zip(y, predictions, strict=True))
        ],
    )
    errors = np.flatnonzero(predictions != np.array(y))
    sampled = sorted(np.random.default_rng(42).choice(errors, min(18, len(errors)), replace=False))
    write_json(
        output.with_name(output.stem + "_error_sample.json"),
        [
            {"test_index": int(i), "gold": LABELS[y[i]], "predicted": LABELS[predictions[i]]}
            for i in sampled
        ],
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, default=Path("reports/test_metrics.json"))
    args = parser.parse_args()
    evaluate(args.artifact_dir, args.output)
