import json
from pathlib import Path

from tweet_sentiment.data import write_json


def read(path):
    return json.loads(Path(path).read_text())


if __name__ == "__main__":
    results = read("artifacts/validation_metrics.json")
    metadata = read("artifacts/metadata.json")
    test = read("reports/test_metrics.json")["official"]
    benchmark = read("reports/benchmark.json")
    audit = read("reports/data_audit.json")
    rows = []
    for result in results:
        m = result["validation"]
        rows.append(
            f"| {result['config']['name']} | {m['accuracy']:.4f} | "
            f"{m['macro_precision']:.4f} | {m['macro_recall']:.4f} | "
            f"{m['macro_f1']:.4f} | {result['train_seconds']:.2f} |"
        )
    per_class = [
        f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | "
        f"{m['f1-score']:.4f} | {int(m['support'])} |"
        for label, m in test["per_class"].items()
    ]
    split_rows = []
    for split, info in audit["splits"].items():
        c = info["class_counts"]
        split_rows.append(
            f"| {split} | {info['count']} | {c['negative']} | {c['neutral']} | {c['positive']} |"
        )
    cm = "\n".join(" ".join(f"{n:5d}" for n in row) for row in test["confusion_matrix"])
    process, http = benchmark["in_process"], benchmark["http_loopback"]
    report = f"""# Evaluation report

Model version {metadata["model_version"]}, selected `{metadata["config"]["name"]}`.
Protocol: [protocol.md](protocol.md); configuration: [experiment.json](../configs/experiment.json).
Artifact: [model.joblib](../artifacts/model.joblib);
metadata: [metadata.json](../artifacts/metadata.json).
Data manifest: [data_manifest.json](data_manifest.json).

Artifact SHA-256: `{metadata["sha256"]}`.
Manifest SHA-256: `{metadata["data_manifest_sha256"]}`.

## Data

TweetEval sentiment, official splits. Labels: 0=negative, 1=neutral, 2=positive.

| Split | Total | Negative | Neutral | Positive |
|---|---:|---:|---:|---:|
{chr(10).join(split_rows)}

No null, raw-empty or normalization-empty records were found, with or without
stop word removal. All rows and split memberships were retained.
Train contains 25 raw duplicate groups (28 excess rows), including 3 groups with
conflicting labels. Normalization increases these to 81 groups (91 excess rows),
20 with conflicting labels. Validation has no internal duplicates. Test has no
raw duplicates, but 5 normalized duplicate groups (9 excess rows), 3 conflicting.
There are 7 shared normalized keys between train and validation (8 train rows,
7 validation rows); one key has conflicting labels. This can slightly favor
validation selection. There are no exact or normalized train/test or val/test
matches. The test subset excluding seen keys is therefore identical to official
test (0 excluded rows). No deduplication or filtering used model predictions.
See [data_audit.json](data_audit.json) for definitions and every pairwise count.

## Validation selection

All learned transformations fit train only. Highest validation macro-F1 wins;
final model is refit on train only, without validation. Seven fixed candidates,
seed 42, one thread. Word TF-IDF uses unigrams/bigrams, min_df=2, max_features=120000,
sublinear TF; char TF-IDF uses lengths 3–5, min_df=3, max_features=120000.
LinearSVC C=1, dual=True; logistic regression C=2. No class weights.

| Candidate | Accuracy | Macro precision | Macro recall | Macro F1 | Train seconds |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

The selected SVM with stop words removed scores 0.6604 versus 0.6410 when retained.
Negations are exempt from removal. Character features do not improve validation
macro-F1 here. This selection exceeds the majority baseline (0.2019 macro-F1).
Full per-class validation metrics and confusion matrices for all candidates are
in [validation_metrics.json](../artifacts/validation_metrics.json).

## Final test

One final test evaluation after model selection. No model changes followed it.
This is our macro-F1 protocol; do not compare it directly with TweetEval's
sentiment leaderboard, which uses a different primary metric (macro recall).

- Accuracy: **{test["accuracy"]:.6f}**
- Macro precision: **{test["macro_precision"]:.6f}**
- Macro recall: **{test["macro_recall"]:.6f}**
- Macro F1: **{test["macro_f1"]:.6f}**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
{chr(10).join(per_class)}

Confusion matrix: rows are gold, columns are predicted; both ordered
negative, neutral, positive.

```text
{cm}
```

Validation macro-F1 exceeds test by 0.0973. Negative recall is weak and many
negative examples become neutral. Train has 15.5% negative and 39.1% positive
examples; test has 32.3% negative and 19.3% positive. This is observed label shift;
it does not establish the cause of the entire quality gap. No accuracy target was
promised or used for tuning. See [error_analysis.md](error_analysis.md) for 18
seeded error inspections and limitations.

## Cost and latency

- Final fit: {metadata["final_train_seconds"]:.3f} seconds;
  artifact: {metadata["artifact_bytes"]:,} bytes.
- CPU: {benchmark["cpu"]}; OS: {benchmark["platform"]}; one CPU thread, batch size 1.
- Five original short inputs; 30 warmups, 500 sequential timings per mode.
- In-process p50/p95: {process["p50_ms"]:.3f}/{process["p95_ms"]:.3f} ms.
- Local HTTP p50/p95: {http["p50_ms"]:.3f}/{http["p95_ms"]:.3f} ms,
  one uvicorn worker, keep-alive, loopback; not a public-network or load benchmark.

[benchmark.json](benchmark.json) records versions and timings. These observations
on one development machine are not a production SLA. Public hosting and container
verification status is recorded separately in [deployment.md](deployment.md).

## Preprocessing and serving limitations

Shared sklearn Pipeline: NFKC, HTML decoding, lowercase, URL/mention tokens,
hashtag word preservation, contraction expansion, tokenization, optional sklearn
English stop words minus no/not/nor/never. Whitespace is collapsed. Words/numbers,
emoticons and Unicode symbols including emoji are retained. Question/exclamation
runs become single/repeated marker tokens; other technical punctuation is removed.
No emoji sentiment dictionary is imposed. Character candidates see the same
normalized string. The selected model uses word n-grams only.

The API supports English, does not detect language and does not supply calibrated
confidence. Unknown vocabulary, sarcasm and missing context remain difficult.
Normalization-empty requests return 422 rather than a prediction. Inputs that
contain tokens outside the learned vocabulary can still receive a default-like
linear prediction; a label alone is not evidence of certainty. Training and serving
use the same serialized pipeline, strict model checksums and pinned dependencies.
"""
    Path("reports/evaluation.md").write_text(report)
    submission = (
        "Built a reproducible English tweet sentiment classifier on TweetEval with "
        "TF-IDF + LinearSVC and a FastAPI API. Official test: accuracy 57.73%, "
        "macro-F1 0.5631. Includes trained model, data checksums, evaluation, tests "
        "and Docker setup. Repository: https://github.com/EshkirenokCode/tweet-sentiment. "
        "Public API deployment is pending."
    )
    assert len(submission) <= 500
    Path("reports/application.txt").write_text(submission + "\n")
    write_json(
        "reports/application_metadata.json", {"characters": len(submission), "public_api": None}
    )
    print("Report written; application characters:", len(submission))
