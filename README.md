# Tweet sentiment

English text classification into `negative`, `neutral`, or `positive`.
MiniLM fine-tuned on TweetEval sentiment, served on CPU through int8 ONNX.
Author: Ilia Gulevskii.

[Live API](https://tweet-sentiment.gulevskii.dev/docs) ·
[Evaluation](reports/evaluation.md) · [Data and model sources](DATA.md)

| Version | Model | Test accuracy | Macro-F1 |
| --- | --- | --- | --- |
| v1.1 | Word TF-IDF + LinearSVC | 57.79% | 0.5637 |
| v1.2 | Fine-tuned MiniLM, int8 | **69.59%** | **0.6924** |

Both use the same 12,284-example official test split. This test was inspected in
previous versions; v1.2 is a repeat measurement. Selection used validation only.

## Run

Python 3.12. The model and tokenizer are committed in `artifacts/`.
Serving downloads neither weights nor data. PyTorch is not needed for inference.

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

Response: `{"label":"positive","model_version":"1.2.0"}`.
`/` redirects to `/docs`; `/health` checks the process, `/ready` checks the model.
Limits: 2000 characters, 256 model tokens and 8192 HTTP-body bytes. Token-overflow
inputs are rejected, never silently truncated. Invalid/empty input returns 422.
The API returns no calibrated confidence score.

## Training

The source is the general `sentence-transformers/all-MiniLM-L6-v2` encoder,
revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, not a TweetEval sentiment
checkpoint. Two CPU training epochs on train; validation selects the epoch and
serving precision. [Protocol](experiments/protocol-v1.2.md), [candidate results](artifacts/validation_metrics.json).

In a fresh checkout, use a separate training environment:

```bash
python3.12 -m venv .venv-train
source .venv-train/bin/activate
python -m pip install -r requirements-training.lock -r requirements.lock
python -m pip install --no-deps .
python -m tweet_sentiment.data download
python experiments/finetune_minilm.py
python experiments/export_minilm.py
python experiments/package_minilm.py --output artifacts/reproduced
python -m tweet_sentiment.evaluate --artifact-dir artifacts/reproduced \
  --output reports/reproduced_test_metrics.json
```

Training and evaluation refuse to overwrite existing outputs. On Linux, choose
CPU-only PyTorch wheels if GPU libraries are not needed. Versions, seed, splits
and source revision are fixed; numerical differences across platforms are possible.
Optional sparse/frozen-feature comparisons are in `experiments/`.

Data split sizes: 45,615 / 2,000 / 12,284. Downloads verify pinned hashes.
Raw texts are not committed. [Duplicate/overlap audit](reports/data_audit.json).
Stop word removal was compared in sparse baselines; the final encoder keeps
function words and negations for context. Both training and serving use the same cleaner.

## Checks

```bash
pytest -q
ruff check src tests scripts experiments
python scripts/http_smoke.py --url http://127.0.0.1:8000
python scripts/benchmark.py
python scripts/make_report.py
```

CI builds and runs Docker and tests the included model without downloading the corpus.
The local latency report uses 30 warmups and 500 single-input measurements per mode.
[Deployment](deploy/README.md), [deployment checks](reports/deployment.md).

## Limits

English only; no language detection. Headlines, sarcasm, mixed sentiment and missing
context remain difficult. [18 sampled errors](reports/error_analysis.md),
[model notes](reports/model_notes.md). A fresh holdout is needed for further development.

Only load trusted joblib artifacts: deserialization executes code. Checksums detect
corruption, not malicious replacement. The pretrained asset license and modification
notice are in `artifacts/encoder/`. Earlier models and reports remain at tags
`v1.0.0` and `v1.1.0`.
