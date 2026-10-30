# v1.1 evaluation protocol

2026-10-30. Correct two preprocessing defects: expand the word `cannot` to
`can not`, and preserve lowercased letter emoticons (`:d`, `:p`) and `8)`.
Keep the seven model configurations, source revision, splits and seed from v1.0.
Select on validation macro-F1, refit on train only, then evaluate the selected
model once. Do not select changes or hyperparameters using test performance.

The test set was evaluated and inspected during v1.0 development. The v1.1 test
result is a repeat measurement on that same set, not a fresh holdout result.
Old metrics and code remain available at Git tag `v1.0.0`. Preprocessing version
is serialized in the pipeline; old artifacts retain their original cleaner.
