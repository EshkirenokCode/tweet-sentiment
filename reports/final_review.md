# Final review — v1.0.0

Reviewed on 2026-10-28. Serving/code revision:
`5e8a7173d4e21f703493220df0deec21e78d7d4f`.

Verdict: a completed, reproducible baseline ML project suitable for a portfolio or
technical assignment. This is not a claim of high sentiment accuracy or production
service guarantees. The model's limits are part of the result, not unfinished setup.

## Verified

- All 25 tests, lint, formatting, dependency checks and data checksums passed.
- [CI](https://github.com/EshkirenokCode/tweet-sentiment/actions/runs/40675369755)
  passed, including Docker build/run and HTTP checks.
- Refitting the selected configuration on the pinned train split reproduced the
  classifier coefficients, vocabulary and validation predictions exactly.
- The frozen artifact reproduced all 12,284 stored test predictions exactly.
  Recomputing metrics from those stored labels reproduced every published metric.
  This was an integrity check; no model selection, preprocessing change or tuning
  was performed during review.
- The deployed model SHA-256 matches the evaluated artifact:
  `2f0278b7a3b346cc2da6f096d2321e14a775fd20d589ac199edbe43643e68a2f`.
- External HTTP smoke passed at https://tweet-sentiment.gulevskii.dev, including
  root redirect to `/docs`, realistic response schema example, health/readiness,
  prediction, invalid input and oversized bodies. HTTPS verification remained on.
- The model container was healthy, its one-CPU/512-MiB limits were present, and
  observed memory was about 155 MiB. Certificate renewal timer was active and its
  last service result was successful. Existing application virtual-host checksums
  remained unchanged; other projects' start times and restart counts did not change.
- No raw dataset files, private key files or actual host environment file are tracked.

## Changes made during review

The API base URL now redirects to interactive documentation instead of showing 404.
The response schema shows a realistic label/model version example. Tests and live
HTTP checks cover both changes. Only this project's API container was recreated;
no shared edge reload or other application restart was needed for this patch.
The model, preprocessing and reported test metrics remain unchanged.

## Limits to disclose

Test accuracy is **57.73%**, macro-F1 **0.5631**; validation macro-F1 **0.6604**.
Negative recall is weak (0.4434). English only; sparse n-grams miss sarcasm,
context and mixed sentiment. The cleaner expands `n't` contractions but loses
`cannot` through stop word removal and some letter emoticons after lowercasing.
Correcting that requires a new trained model and an explicitly disclosed repeat
evaluation, since the original test has already been inspected.

This is a strong example of completing the engineering workflow around a simple
model. It should be presented as a measured baseline, not a state-of-the-art model
or evidence that sentiment analysis is solved. For a portfolio, link the repository
and the live docs together. Training/evaluation details and interview notes are
already included; no additional frontend is required to demonstrate the API.
