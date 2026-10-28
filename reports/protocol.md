# Evaluation protocol

Fixed before training on 2026-10-28. Seed 42; one CPU thread. Use the official
TweetEval sentiment train/val/test files at revision
`4fbd22cd78421f05b1ecdb4fc5725bc7a7bd8f66`. The upstream plain-text files are the
primary download route, avoiding a remote dataset script and Parquet conversion.

Seven predeclared candidates in `configs/experiment.json`: majority dummy,
word TF-IDF logistic regression with/without stop words, word TF-IDF LinearSVC
with/without stop words, word+character TF-IDF LinearSVC with/without stop words.
Only train fits vocabulary, IDF and weights. Select highest validation macro-F1;
ties follow config order. Refit that configuration on train only. No tuning on test.

Preserve official split membership and all valid rows, including duplicates.
Invalid labels, missing texts or inconsistent counts abort download. Report raw
and normalized duplicate groups, conflicting labels and cross-split overlaps.
The primary result uses the complete official test; a second result excludes
test keys seen in train OR validation, determined without looking at predictions.
Normalization for overlap uses the shared cleaner without stop word removal.

After selection, run test evaluation once and save predictions (IDs/labels only),
macro metrics, per-class metrics, and confusion matrix in label order
negative/neutral/positive. Inspect 18 errors selected by seeded random sampling
from all errors. This analysis must not trigger model changes in this version.

Benchmark 30 warmups and 500 batch-one predictions, separately in process and
over local HTTP. Record p50/p95, machine, versions, threads and artifact size.
