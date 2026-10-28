# Evaluation report

Model version 1.0.0, selected `svc_words_stop`.
Protocol: [protocol.md](protocol.md); configuration: [experiment.json](../configs/experiment.json).
Artifact: [model.joblib](../artifacts/model.joblib);
metadata: [metadata.json](../artifacts/metadata.json).
Data manifest: [data_manifest.json](data_manifest.json).

Artifact SHA-256: `2f0278b7a3b346cc2da6f096d2321e14a775fd20d589ac199edbe43643e68a2f`.
Manifest SHA-256: `d01a95d44d4e2d7bdd89ea11d5267d10c4b45b5b94a245d20783ba441f9158ad`.

## Data

TweetEval sentiment, official splits. Labels: 0=negative, 1=neutral, 2=positive.

| Split | Total | Negative | Neutral | Positive |
|---|---:|---:|---:|---:|
| train | 45615 | 7093 | 20673 | 17849 |
| val | 2000 | 312 | 869 | 819 |
| test | 12284 | 3972 | 5937 | 2375 |

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
| dummy | 0.4345 | 0.1448 | 0.3333 | 0.2019 | 1.31 |
| lr_words_stop | 0.6945 | 0.6788 | 0.6405 | 0.6535 | 3.26 |
| lr_words_keep | 0.6910 | 0.6722 | 0.6358 | 0.6481 | 3.47 |
| svc_words_stop | 0.6880 | 0.6751 | 0.6504 | 0.6604 | 1.34 |
| svc_words_keep | 0.6715 | 0.6512 | 0.6336 | 0.6410 | 1.86 |
| svc_wordchar_stop | 0.6805 | 0.6598 | 0.6447 | 0.6512 | 6.76 |
| svc_wordchar_keep | 0.6815 | 0.6611 | 0.6454 | 0.6521 | 8.59 |

The selected SVM with stop words removed scores 0.6604 versus 0.6410 when retained.
Negations are exempt from removal. Character features do not improve validation
macro-F1 here. This selection exceeds the majority baseline (0.2019 macro-F1).
Full per-class validation metrics and confusion matrices for all candidates are
in [validation_metrics.json](../artifacts/validation_metrics.json).

## Final test

One final test evaluation after model selection. No model changes followed it.
This is our macro-F1 protocol; do not compare it directly with TweetEval's
sentiment leaderboard, which uses a different primary metric (macro recall).

- Accuracy: **0.577336**
- Macro precision: **0.570825**
- Macro recall: **0.573739**
- Macro F1: **0.563088**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| negative | 0.6305 | 0.4434 | 0.5206 | 3972 |
| neutral | 0.6019 | 0.6446 | 0.6225 | 5937 |
| positive | 0.4801 | 0.6333 | 0.5461 | 2375 |

Confusion matrix: rows are gold, columns are predicted; both ordered
negative, neutral, positive.

```text
 1761  1779   432
  913  3827  1197
  119   752  1504
```

Validation macro-F1 exceeds test by 0.0973. Negative recall is weak and many
negative examples become neutral. Train has 15.5% negative and 39.1% positive
examples; test has 32.3% negative and 19.3% positive. This is observed label shift;
it does not establish the cause of the entire quality gap. No accuracy target was
promised or used for tuning. See [error_analysis.md](error_analysis.md) for 18
seeded error inspections and limitations.

## Cost and latency

- Final fit: 1.355 seconds;
  artifact: 2,304,931 bytes.
- CPU: Apple M4 Pro; OS: macOS-26.6.2-arm64-arm-64bit; one CPU thread, batch size 1.
- Five original short inputs; 30 warmups, 500 sequential timings per mode.
- In-process p50/p95: 0.187/0.197 ms.
- Local HTTP p50/p95: 0.708/0.845 ms,
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

Final source audit: the frozen v1 cleaner does not expand `cannot`, which the
stop word list removes, and lowercasing can discard letter emoticons such as `:D`.
These bounded preprocessing limitations are disclosed rather than changing the
published model after test inspection. A correction requires a new trained model,
new metrics and explicit disclosure that the original test has already been used.
