# Tweet sentiment

English text classification into `negative`, `neutral`, or `positive`.
Word TF-IDF + LinearSVC on TweetEval sentiment. Author: Ilia Gulevskii.

[Live API](https://tweet-sentiment.gulevskii.dev/docs) ·
[Evaluation](reports/evaluation.md) · [Data source and conditions](DATA.md)

v1.1.0: validation macro-F1 **0.6592**; test accuracy **57.79%**, macro-F1 **0.5637**
on 12,284 examples. Negative recall is **0.4439**. This revision fixes preprocessing
and repeats evaluation on the test already inspected in v1.0; it is not a fresh holdout.

## Run

Python 3.12. The trained model is in `artifacts/`; serving needs no data download.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps .
uvicorn tweet_sentiment.api:app --host 127.0.0.1 --port 8000 --workers 1 --limit-concurrency 16 --no-access-log
```

```bash
curl -H 'Content-Type: application/json' \
  -d '{"text":"I love this wonderful app!"}' http://127.0.0.1:8000/predict
```

Response: `{"label":"positive","model_version":"1.1.0"}`.
`/` opens `/docs`; `/health` checks the process and `/ready` checks the model.
Invalid, blank or normalization-empty text returns 422. The limits are 2000 text
characters and 8192 HTTP-body bytes. The response contains no confidence estimate.

## Reproduce

Seven fixed configurations, seed 42; selection by validation macro-F1. Vocabulary,
IDF and classifier fit train only. The final model is also trained on train only.
[Original protocol](reports/protocol.md), [v1.1 changes](reports/protocol-v1.1.md).

```bash
python -m tweet_sentiment.data download
python -m tweet_sentiment.data verify
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  python -m tweet_sentiment.train --artifact-dir artifacts/reproduced
python -m tweet_sentiment.evaluate --artifact-dir artifacts/reproduced \
  --output reports/reproduced_test_metrics.json
```

Download uses a pinned source commit and checksums. Split sizes are
45,615 / 2,000 / 12,284. Raw data is not committed. Duplicates, conflicting labels,
empty texts and split overlaps are counted in [data_audit.json](reports/data_audit.json).
Training and evaluation refuse to overwrite existing artifacts/results.

## Checks

```bash
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python scripts/http_smoke.py --url http://127.0.0.1:8000
python scripts/benchmark.py
python scripts/make_report.py
```

The benchmark uses 30 warmups and 500 batch-one calls, separately in process and
over local HTTP. CI runs tests, lint and a Docker build/HTTP check without the corpus.
[Deployment and maintenance](deploy/README.md), [deployment checks](reports/deployment.md).

## Limits

English only; no language detection. Local word patterns miss sarcasm, negation
scope and conversational context. The validation/test gap is about 0.10 macro-F1.
See the [18 sampled errors](reports/error_analysis.md) and [model notes](reports/model_notes.md).
Future improvements need a new holdout or disclosure of further test reuse.

Only load the repository's trusted joblib artifact: deserialization executes code.
Its checksum detects corruption, not malicious replacement. No tweet corpus or
private server files are included. v1.0 code and results remain at tag `v1.0.0`.
