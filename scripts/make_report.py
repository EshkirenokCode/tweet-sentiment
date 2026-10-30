import json
from pathlib import Path

from tweet_sentiment.data import write_json


def read(path):
    return json.loads(Path(path).read_text())


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        ]
    )


def make_report():
    metadata = read("artifacts/metadata.json")
    results = read("artifacts/validation_metrics.json")
    evaluation = read("reports/test_metrics.json")
    benchmark = read("reports/benchmark.json")
    audit = read("reports/data_audit.json")
    if not (metadata["sha256"] == evaluation["artifact_sha256"] == benchmark["model_sha256"]):
        raise ValueError("Model, evaluation and benchmark refer to different artifacts")
    test = evaluation["official"]
    winner = max(results, key=lambda row: row["validation"]["macro_f1"])
    splits = table(
        ["Split", "Rows", "Negative", "Neutral", "Positive"],
        [
            [split, row["count"], *[row["class_counts"][label] for label in test["label_order"]]]
            for split, row in audit["splits"].items()
        ],
    )
    duplicates = table(
        ["Split", "Key", "Duplicate groups", "Extra rows", "Conflicting groups"],
        [
            [
                split,
                mode,
                row[mode]["duplicate_groups"],
                row[mode]["excess_rows"],
                row[mode]["conflicting_label_groups"],
            ]
            for split, row in audit["splits"].items()
            for mode in ("raw", "normalized")
        ],
    )
    overlap = table(
        ["Key", "Splits", "Shared keys", "First rows", "Second rows", "Conflicts"],
        [
            [
                mode,
                pair,
                row["shared_keys"],
                row["rows_in_first"],
                row["rows_in_second"],
                row["conflicting_label_keys"],
            ]
            for mode, pairs in audit["overlaps"].items()
            for pair, row in pairs.items()
        ],
    )
    validation = table(
        ["Candidate", "Accuracy", "Macro precision", "Macro recall", "Macro F1", "Fit seconds"],
        [
            [
                row["config"]["name"],
                *[
                    f"{row['validation'][key]:.4f}"
                    for key in ("accuracy", "macro_precision", "macro_recall", "macro_f1")
                ],
                f"{row['train_seconds']:.2f}",
            ]
            for row in results
        ],
    )
    classes = table(
        ["Class", "Precision", "Recall", "F1", "Support"],
        [
            [
                label,
                *[f"{row[key]:.4f}" for key in ("precision", "recall", "f1-score")],
                int(row["support"]),
            ]
            for label, row in test["per_class"].items()
        ],
    )
    matrix = "\n".join(" ".join(f"{x:5d}" for x in row) for row in test["confusion_matrix"])
    latency = table(
        ["Mode", "p50 ms", "p95 ms", "Measurements"],
        [
            [
                mode,
                f"{benchmark[mode]['p50_ms']:.3f}",
                f"{benchmark[mode]['p95_ms']:.3f}",
                benchmark[mode]["measurements"],
            ]
            for mode in ("in_process", "http_loopback")
        ],
    )
    report = f"""# Evaluation

Model {metadata["model_version"]}: `{metadata["config"]["name"]}`.
[Configuration](../configs/experiment.json), [data manifest](data_manifest.json),
[model metadata](../artifacts/metadata.json).

Artifact SHA-256: `{metadata["sha256"]}`.

## Protocol

The v1.1 revision fixes `cannot` expansion and letter-emoticon tokenization.
The seven candidates, official splits and seed 42 are unchanged. Vocabulary, IDF
and weights fit train only. Select by validation macro-F1 and refit on train only.
The test was already evaluated and inspected in v1.0: the numbers below are a
repeat measurement, not a new untouched holdout. No test-based parameter search
was performed. See [protocol-v1.1.md](protocol-v1.1.md); v1.0 is kept at Git tag `v1.0.0`.

## Data

TweetEval sentiment; labels 0=negative, 1=neutral, 2=positive.

{splits}

{duplicates}

{overlap}

All official rows were retained. Empty raw/normalized counts are recorded in
[data_audit.json](data_audit.json); invalid rows abort loading. Normalized overlap
keys use the cleaner without stop word removal. Shared train/validation keys can
favor selection slightly. Test rows matching train or validation are excluded only
from the secondary result: {evaluation["excluded_overlap_rows"]} rows excluded.

## Validation

{validation}

Selected `{winner["config"]["name"]}` by macro-F1 {winner["validation"]["macro_f1"]:.4f}.
Per-class results and confusion matrices for every candidate are in
[validation_metrics.json](../artifacts/validation_metrics.json).

## Test

Accuracy: **{test["accuracy"]:.6f}**. Macro precision: **{test["macro_precision"]:.6f}**.
Macro recall: **{test["macro_recall"]:.6f}**. Macro F1: **{test["macro_f1"]:.6f}**.

{classes}

Rows = gold; columns = predicted. Both orders: negative, neutral, positive.

```text
{matrix}
```

Validation/test macro-F1 gap: {winner["validation"]["macro_f1"] - test["macro_f1"]:.4f}.
Negative recall remains weak. Class balance differs across splits; the error sample
also shows context and target-selection failures. [Error analysis](error_analysis.md).
Machine-readable results: [test_metrics.json](test_metrics.json).

## Runtime

Final fit: {metadata["final_train_seconds"]:.3f} seconds.
Artifact: {metadata["artifact_bytes"]:,} bytes.
{benchmark["cpu"]}, {benchmark["platform"]}; one thread, batch size 1,
30 warmups, five original short inputs. HTTP uses one worker and loopback keep-alive.

{latency}

These are development-machine measurements, not server capacity estimates.
[Benchmark details](benchmark.json), [deployment](deployment.md).

## Limits

English only, no language detection or calibrated probability. Word n-grams miss
sarcasm, negation scope and conversational context. Inputs empty after cleaning
are rejected; unknown vocabulary can still produce a label from the linear model.
"""
    Path("reports/evaluation.md").write_text(report)
    submission = (
        f"English tweet sentiment API using TF-IDF + LinearSVC on TweetEval. "
        f"v{metadata['model_version']} test: accuracy {test['accuracy']:.2%}, "
        f"macro-F1 {test['macro_f1']:.4f} (same test set inspected in v1.0). "
        "Code, model, metrics and Docker: https://github.com/EshkirenokCode/tweet-sentiment. "
        "API: https://tweet-sentiment.gulevskii.dev/docs"
    )
    assert len(submission) <= 500
    Path("reports/application.txt").write_text(submission + "\n")
    write_json(
        "reports/application_metadata.json",
        {
            "characters": len(submission),
            "public_api": "https://tweet-sentiment.gulevskii.dev",
        },
    )
    print("Report written; application characters:", len(submission))


if __name__ == "__main__":
    make_report()
