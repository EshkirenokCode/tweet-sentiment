# Model notes

- TweetEval provides fixed English sentiment splits and a published three-label mapping.
- Word TF-IDF + LinearSVC fits quickly on CPU. Seven configurations are compared
  on validation macro-F1; the selected configuration is refit on train only.
- Macro-F1 gives each class equal weight. Accuracy alone can hide poor negative recall.
- Vocabulary and IDF are learned inside the pipeline on train only. Duplicates and
  split overlaps are counted separately; validation is not added to training.
- Stop words are removed except `no`, `not`, `nor`, `never`. Contraction expansion
  and token retention preserve cues but do not model negation scope or sarcasm.
- SVM decision margins are not probabilities. The API returns no confidence value.
- v1.1 fixes the cleaner and repeats evaluation on the test set already inspected
  in v1.0. It does not provide a new independent holdout result.
