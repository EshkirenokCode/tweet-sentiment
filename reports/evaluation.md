# Evaluation

Model 1.2.0: `minilm_finetuned_int8`.
[Training recipe](../experiments/protocol-v1.2.md), [data manifest](data_manifest.json),
[model metadata](../artifacts/metadata.json).

Artifact SHA-256: `607d4ca17d8bde0b2209abacd6adc82c2333c098f4b20edf25fb642d7196eeec`.

## Protocol

v1.2 fine-tunes the general sentence encoder `sentence-transformers/all-MiniLM-L6-v2`
(revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) on TweetEval train.
Two epochs, batch 32, AdamW lr=3e-5, weight decay 0.01, 10% warmup, seed 42,
four CPU threads. Epoch 2 had the highest validation macro-F1. Stop words are kept.

Eight sparse and six frozen-feature candidates were also compared on validation.
The selected checkpoint was exported to ONNX and dynamically quantized. Int8 was
preferred if its batch-one validation macro-F1 was within 0.005 of float; the
observed drop was 0.0016.
No test results were used to select the family, epoch or serving precision.

The official test was already used in v1.0/v1.1. These are repeat measurements,
not a fresh holdout. Earlier code and results remain at tag `v1.1.0`.
[Protocol and candidates](../experiments/protocol-v1.2.md),
[training parameters](experiments/training.json),
[pretrained asset notice](../artifacts/encoder/NOTICE).

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
| v1.1_word_svc | 0.6875 | 0.6739 | 0.6493 | 0.6592 | 1.33 |
| nb_words_keep_C1 | 0.6665 | 0.7006 | 0.5740 | 0.5871 | 1.68 |
| nb_words_keep_C4 | 0.6900 | 0.6945 | 0.6196 | 0.6374 | 1.82 |
| nb_words_stop_C1 | 0.6750 | 0.6979 | 0.5870 | 0.6020 | 1.38 |
| nb_words_stop_C4 | 0.6910 | 0.6936 | 0.6225 | 0.6401 | 1.46 |
| nb_wordchar_keep_C1 | 0.6895 | 0.7051 | 0.6127 | 0.6311 | 9.18 |
| nb_wordchar_keep_C4 | 0.7050 | 0.6993 | 0.6452 | 0.6616 | 10.60 |
| svc_wordchar_balanced | 0.6955 | 0.6694 | 0.6825 | 0.6750 | 6.26 |
| lr_wordchar_balanced | 0.6840 | 0.6563 | 0.6695 | 0.6620 | 22.00 |
| embeddings_C1_None | 0.6780 | 0.6672 | 0.6396 | 0.6502 | 0.56 |
| embeddings_C10_None | 0.6745 | 0.6626 | 0.6396 | 0.6486 | 0.34 |
| embeddings_C100_None | 0.6805 | 0.6696 | 0.6430 | 0.6533 | 0.58 |
| hybrid_C0.1_None | 0.7070 | 0.6931 | 0.6655 | 0.6764 | 2.10 |
| hybrid_C1_None | 0.6785 | 0.6599 | 0.6494 | 0.6542 | 7.87 |
| hybrid_C0.1_balanced | 0.7050 | 0.6787 | 0.6982 | 0.6864 | 2.23 |
| minilm_epoch_1_float | 0.7155 | 0.7021 | 0.6937 | 0.6977 | 165.16 |
| minilm_epoch_2_float | 0.7205 | 0.7064 | 0.7064 | 0.7064 | 331.82 |
| minilm_finetuned_int8 | 0.7235 | 0.7196 | 0.6946 | 0.7048 | 331.85 |

Selected `minilm_finetuned_int8` by macro-F1 0.7048.
Per-class results and confusion matrices for every candidate are in
[validation_metrics.json](../artifacts/validation_metrics.json).

## Test

The headline test metrics were measured in the Linux x86-64 deployment container,
with one CPU thread and batch size 1. Dynamic int8 results vary slightly across
CPU architectures: the developer's ARM machine scored 69.59% accuracy / 0.6924 F1.
The server validation macro-F1 is 0.7018 (ARM: 0.7048); 52 of 2,000 validation
predictions differ. [Platform check](experiments/server_parity.json).
No weights, checkpoint or precision were changed after this check.

Compared with v1.1, accuracy changed from 57.79% to 69.68%
and macro-F1 from 0.5637 to 0.6928.
That is 11.89 percentage points of accuracy
and 1461 additional
correct predictions.

Accuracy: **0.696841**. Macro precision: **0.691367**.
Macro recall: **0.695409**. Macro F1: **0.692768**.

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| negative | 0.7256 | 0.6770 | 0.7004 | 3972 |
| neutral | 0.6995 | 0.7086 | 0.7040 | 5937 |
| positive | 0.6490 | 0.7006 | 0.6738 | 2375 |

Rows = gold; columns = predicted. Both orders: negative, neutral, positive.

```text
 2689  1141   142
  972  4207   758
   45   666  1664
```

Validation/test macro-F1 gap: 0.0120.
Negative recall improved from 0.4439 to
0.6770. Class balance differs across splits;
context and annotation ambiguity still cause errors. [Error analysis](error_analysis.md).
Machine-readable results: [test_metrics.json](test_metrics.json).

## Runtime

Local fine-tuning: 331.848 seconds.
Inference files: 23,730,241 bytes. Training used four CPU threads.
Apple M4 Pro, macOS-26.6.2-arm64-arm-64bit; one thread, batch size 1,
30 warmups, five original short inputs. HTTP uses one worker and loopback keep-alive.

| Mode | p50 ms | p95 ms | Measurements |
| --- | --- | --- | --- |
| in_process | 0.709 | 0.997 | 500 |
| http_loopback | 1.326 | 1.644 | 500 |

These are development-machine measurements, not server capacity estimates.
[Benchmark details](benchmark.json), [deployment](deployment.md).

## Limits

English only, no language detection or calibrated probability. Sarcasm, mixed sentiment
and missing context remain difficult. The API rejects inputs over 256 model tokens
rather than silently truncating. Inputs empty after cleaning are rejected;
out-of-domain inputs can still receive an unreliable label.
