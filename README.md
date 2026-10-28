# Tweet sentiment

English text classification into `negative`, `neutral`, or `positive`.
Word TF-IDF + LinearSVC, trained on the official TweetEval sentiment train split.
Author: Ilia Gulevskii.

Validation macro-F1: **0.6604**. Official test: **57.73% accuracy**, **0.5631 macro-F1**
(12,284 examples). The validation/test gap is material; negative recall is 0.4434.
See the [evaluation report](reports/evaluation.md) and [error analysis](reports/error_analysis.md).

## Run

Python 3.12. The evaluated model is committed in `artifacts/`; no dataset download
or training is required to serve it. Install the exact dependency lock first.

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

Response: `{"label":"positive","model_version":"1.0.0"}`.
`GET /health` checks the process; `GET /ready` returns 503 if the model cannot load.
Interactive documentation: `http://127.0.0.1:8000/docs`.
The API rejects invalid/blank/normalization-empty input, strings over 2000 characters,
and HTTP bodies over 8192 bytes. Labels have no calibrated confidence.

Public HTTPS API: **https://tweet-sentiment.gulevskii.dev**.
[Interactive API docs](https://tweet-sentiment.gulevskii.dev/docs).
The loopback URL above is for local development.
[Deployment instructions and limits](deploy/README.md), [verification status](reports/deployment.md).

## Reproduce

[Protocol](reports/protocol.md) and [seven configurations](configs/experiment.json)
were fixed before experiments. Vocabulary, IDF and classifier fit train only;
validation selects the model; test is evaluated after selection. Seed 42, one thread.
The selected stop word removal preserves negations and outperformed keeping stop words.

```bash
python -m tweet_sentiment.data download
python -m tweet_sentiment.data verify
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  python -m tweet_sentiment.train --artifact-dir artifacts/reproduced
python -m tweet_sentiment.evaluate --artifact-dir artifacts/reproduced \
  --output reports/reproduced_test_metrics.json
```

The default train/evaluate commands refuse to overwrite the published artifact or
test metrics. Reproduction writes separate outputs; tiny numerical differences across
platforms are possible. Downloads use a pinned upstream commit and verified SHA-256.
Official split sizes: 45,615 / 2,000 / 12,284. No raw corpus is committed.
There are 7 normalized train/validation overlaps and none between train/test;
all rows are retained and duplicate/label conflicts are [reported](reports/data_audit.json).
See [provenance and data conditions](DATA.md) before using or redistributing data.

```bash
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python scripts/http_smoke.py --url http://127.0.0.1:8000
python scripts/benchmark.py
python scripts/make_report.py
```

Benchmark: 500 batch-one measurements after warmup, separately in process and over
local HTTP. Apple M4 Pro: about 0.19 ms / 0.71 ms p50 respectively; not a hosting SLA.
CI runs lint, tests and a Docker build/HTTP smoke test without downloading the corpus.

## Limits

English only; no language detection. Sparse n-grams miss sarcasm, negation scope,
mixed sentiment, entity-specific stance and conversational context. Label balance
differs across splits. The test set has been inspected for error analysis; any later
improvements must disclose its reuse. Load only the trusted repository artifact:
joblib is executable serialization, and its checksum is a corruption check, not authentication.

[Interview notes](reports/interview.md) and a [short submission text](reports/application.txt)
are included. Nothing has been sent to the employer.
