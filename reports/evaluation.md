# Evaluation

Model 1.1.0: `svc_words_stop`.
[Configuration](../configs/experiment.json), [data manifest](data_manifest.json),
[model metadata](../artifacts/metadata.json).

Artifact SHA-256: `29cc3e5ee08500693bc09c8f3d07de69ac1ec678431967d257fb170723fc42f1`.

## Protocol

The v1.1 revision fixes `cannot` expansion and letter-emoticon tokenization.
The seven candidates, official splits and seed 42 are unchanged. Vocabulary, IDF
and weights fit train only. Select by validation macro-F1 and refit on train only.
The test was already evaluated and inspected in v1.0: the numbers below are a
repeat measurement, not a new untouched holdout. No test-based parameter search
was performed. See [protocol-v1.1.md](protocol-v1.1.md); v1.0 is kept at Git tag `v1.0.0`.

## Data

TweetEval sentiment; labels 0=negative, 1=neutral, 2=positive.

| Split | Rows | Negative | Neutral | Positive |
| --- | --- | --- | --- | --- |
| train | 45615 | 7093 | 20673 | 17849 |
| val | 2000 | 312 | 869 | 819 |
| test | 12284 | 3972 | 5937 | 2375 |

| Split | Key | Duplicate groups | Extra rows | Conflicting groups |
| --- | --- | --- | --- | --- |
| train | raw | 25 | 28 | 3 |
| train | normalized | 81 | 91 | 20 |
| val | raw | 0 | 0 | 0 |
| val | normalized | 0 | 0 | 0 |
| test | raw | 0 | 0 | 0 |
| test | normalized | 5 | 9 | 3 |

| Key | Splits | Shared keys | First rows | Second rows | Conflicts |
| --- | --- | --- | --- | --- | --- |
| raw | train/val | 0 | 0 | 0 | 0 |
| raw | train/test | 0 | 0 | 0 | 0 |
| raw | val/test | 0 | 0 | 0 | 0 |
| normalized | train/val | 7 | 8 | 7 | 1 |
| normalized | train/test | 0 | 0 | 0 | 0 |
| normalized | val/test | 0 | 0 | 0 | 0 |

All official rows were retained. Empty raw/normalized counts are recorded in
[data_audit.json](data_audit.json); invalid rows abort loading. Normalized overlap
keys use the cleaner without stop word removal. Shared train/validation keys can
favor selection slightly. Test rows matching train or validation are excluded only
from the secondary result: 0 rows excluded.

## Validation

| Candidate | Accuracy | Macro precision | Macro recall | Macro F1 | Fit seconds |
| --- | --- | --- | --- | --- | --- |
| dummy | 0.4345 | 0.1448 | 0.3333 | 0.2019 | 1.29 |
| lr_words_stop | 0.6920 | 0.6749 | 0.6386 | 0.6511 | 2.81 |
| lr_words_keep | 0.6920 | 0.6766 | 0.6364 | 0.6496 | 4.50 |
| svc_words_stop | 0.6875 | 0.6739 | 0.6493 | 0.6592 | 1.44 |
| svc_words_keep | 0.6760 | 0.6542 | 0.6371 | 0.6443 | 1.75 |
| svc_wordchar_stop | 0.6830 | 0.6631 | 0.6479 | 0.6544 | 6.45 |
| svc_wordchar_keep | 0.6845 | 0.6645 | 0.6492 | 0.6557 | 8.15 |

Selected `svc_words_stop` by macro-F1 0.6592.
Per-class results and confusion matrices for every candidate are in
[validation_metrics.json](../artifacts/validation_metrics.json).

## Test

Accuracy: **0.577906**. Macro precision: **0.571288**.
Macro recall: **0.574020**. Macro F1: **0.563670**.

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| negative | 0.6296 | 0.4439 | 0.5207 | 3972 |
| neutral | 0.6019 | 0.6458 | 0.6231 | 5937 |
| positive | 0.4823 | 0.6324 | 0.5473 | 2375 |

Rows = gold; columns = predicted. Both orders: negative, neutral, positive.

```text
 1763  1781   428
  919  3834  1184
  118   755  1502
```

Validation/test macro-F1 gap: 0.0955.
Negative recall remains weak. Class balance differs across splits; the error sample
also shows context and target-selection failures. [Error analysis](error_analysis.md).
Machine-readable results: [test_metrics.json](test_metrics.json).

## Runtime

Final fit: 1.332 seconds.
Artifact: 2,304,780 bytes.
Apple M4 Pro, macOS-26.6.2-arm64-arm-64bit; one thread, batch size 1,
30 warmups, five original short inputs. HTTP uses one worker and loopback keep-alive.

| Mode | p50 ms | p95 ms | Measurements |
| --- | --- | --- | --- |
| in_process | 0.179 | 0.193 | 500 |
| http_loopback | 0.735 | 0.912 | 500 |

These are development-machine measurements, not server capacity estimates.
[Benchmark details](benchmark.json), [deployment](deployment.md).

## Limits

English only, no language detection or calibrated probability. Word n-grams miss
sarcasm, negation scope and conversational context. Inputs empty after cleaning
are rejected; unknown vocabulary can still produce a label from the linear model.
