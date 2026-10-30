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
    winner = {
        "config": metadata["config"],
        "validation": metadata["selection"]["selected"]["validation"],
    }
    baseline = read("reports/baseline_v1.1.json")["test"]
    float_f1 = read("reports/experiments/precision_validation.json")[0]["validation"]["macro_f1"]
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
[Training recipe](../experiments/protocol-v1.2.md), [data manifest](data_manifest.json),
[model metadata](../artifacts/metadata.json).

Artifact SHA-256: `{metadata["sha256"]}`.

## Protocol

v1.2 fine-tunes the general sentence encoder `sentence-transformers/all-MiniLM-L6-v2`
(revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) on TweetEval train.
Two epochs, batch 32, AdamW lr=3e-5, weight decay 0.01, 10% warmup, seed 42,
four CPU threads. Epoch 2 had the highest validation macro-F1. Stop words are kept.

Eight sparse and six frozen-feature candidates were also compared on validation.
The selected checkpoint was exported to ONNX and dynamically quantized. Int8 was
preferred if its batch-one validation macro-F1 was within 0.005 of float; the
observed drop was {float_f1 - winner["validation"]["macro_f1"]:.4f}.
No test results were used to select the family, epoch or serving precision.

The official test was already used in v1.0/v1.1. These are repeat measurements,
not a fresh holdout. Earlier code and results remain at tag `v1.1.0`.
[Protocol and candidates](../experiments/protocol-v1.2.md),
[training parameters](experiments/training.json),
[pretrained asset notice](../artifacts/encoder/NOTICE).

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

The headline test metrics were measured in the Linux x86-64 deployment container,
with one CPU thread and batch size 1. Dynamic int8 results vary slightly across
CPU architectures: the developer's ARM machine scored 69.59% accuracy / 0.6924 F1.
The server validation macro-F1 is 0.7018 (ARM: 0.7048); 52 of 2,000 validation
predictions differ. [Platform check](experiments/server_parity.json).
No weights, checkpoint or precision were changed after this check.

Compared with v1.1, accuracy changed from {baseline["accuracy"]:.2%} to {test["accuracy"]:.2%}
and macro-F1 from {baseline["macro_f1"]:.4f} to {test["macro_f1"]:.4f}.
That is {(test["accuracy"] - baseline["accuracy"]) * 100:.2f} percentage points of accuracy
and {round((test["accuracy"] - baseline["accuracy"]) * test["count"])} additional
correct predictions.

Accuracy: **{test["accuracy"]:.6f}**. Macro precision: **{test["macro_precision"]:.6f}**.
Macro recall: **{test["macro_recall"]:.6f}**. Macro F1: **{test["macro_f1"]:.6f}**.

{classes}

Rows = gold; columns = predicted. Both orders: negative, neutral, positive.

```text
{matrix}
```

Validation/test macro-F1 gap: {winner["validation"]["macro_f1"] - test["macro_f1"]:.4f}.
Negative recall improved from {baseline["per_class"]["negative"]["recall"]:.4f} to
{test["per_class"]["negative"]["recall"]:.4f}. Class balance differs across splits;
context and annotation ambiguity still cause errors. [Error analysis](error_analysis.md).
Machine-readable results: [test_metrics.json](test_metrics.json).

## Runtime

Local fine-tuning: {metadata["final_train_seconds"]:.3f} seconds.
Inference files: {metadata["artifact_bytes"]:,} bytes. Training used four CPU threads.
{benchmark["cpu"]}, {benchmark["platform"]}; one thread, batch size 1,
30 warmups, five original short inputs. HTTP uses one worker and loopback keep-alive.

{latency}

These are development-machine measurements, not server capacity estimates.
[Benchmark details](benchmark.json), [deployment](deployment.md).

## Limits

English only, no language detection or calibrated probability. Sarcasm, mixed sentiment
and missing context remain difficult. The API rejects inputs over 256 model tokens
rather than silently truncating. Inputs empty after cleaning are rejected;
out-of-domain inputs can still receive an unreliable label.
"""
    Path("reports/evaluation.md").write_text(report)
    submission = (
        f"English tweet sentiment API using MiniLM fine-tuned on TweetEval train. "
        f"v{metadata['model_version']} test: accuracy {test['accuracy']:.2%}, "
        f"macro-F1 {test['macro_f1']:.4f} (test set inspected in earlier versions). "
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
