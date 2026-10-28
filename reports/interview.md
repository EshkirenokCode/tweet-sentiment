# Interview notes

- **Why TweetEval?** It is a real three-class English Twitter benchmark with fixed
  splits and a published label mapping. We pin the source revision and verify hashes.
- **Why TF-IDF and LinearSVC?** Sparse n-grams train quickly on CPU and give a small,
  inspectable baseline. Seven configurations were compared; word SVM with stop word
  removal won on validation macro-F1. Character features did not improve it.
- **How is leakage controlled?** The sklearn Pipeline fits vocabulary, IDF and
  coefficients on train only. Validation selects among fixed candidates. Final refit
  also uses train only. Test is evaluated after selection; duplicate overlap is audited.
  Seven normalized train/validation matches are disclosed; there are no train/test matches.
- **What is macro-F1?** Compute F1 separately for each class and average the three
  equally. It reveals weak negative performance that a majority-heavy accuracy can hide.
  It is not the same as taking F1 from macro-averaged precision and recall.
- **What are the results?** Validation macro-F1 0.6604, test accuracy 0.5773,
  macro-F1 0.5631. Test negative recall is only 0.4434. The validation/test gap is
  material; label balance and domains differ, and the error sample exposes context limits.
- **Why preserve negations?** Removing `not` can invert meaning. Contractions are
  expanded before stop word removal. Preservation is necessary but does not teach
  the classifier the full scope of negation or sarcasm.
- **Why no confidence?** An SVM margin is a signed decision score, not a calibrated
  probability. This API returns only a label and model version. Calibration needs
  its own evaluation on data separate from model fitting and final testing.
- **How does serving work?** Load and checksum the trusted artifact once at startup;
  verify dependency versions. `/health` checks the process; `/ready` checks model
  availability. Reject malformed, blank, oversized and normalization-empty input.
- **What would improve it?** Test class weighting, better treatment of negation and
  context, or a compact pretrained model with an explicit CPU cost comparison.
  Do not silently tune against the already inspected test set.
- **What does the benchmark mean?** Five original short sentences, 30 warmups and
  500 sequential batch-one calls. In-process and loopback HTTP are measured separately
  on an Apple M4 Pro using one thread. These numbers are not a hosting SLA or load test.
