# API review — 2026-11-04

API release 1.2.1 retains model 1.2.0. Weights, tokenizer, normalization and
classification arithmetic are unchanged; this review did not retrain or rescore
the model. The previously measured Linux accuracy remains a model measurement.

## Confirmed defects and fixes

- JSON numeric NaN/Infinity and escaped lone Unicode surrogates caused HTTP 500
  while serializing validation errors. Responses now return 422 with type,
  location and explanation. Submitted values and exception context are omitted.
  Surrogate escapes in extra field names are also handled.
- Concurrent first use of a deserialized classifier could initialize several
  ONNX sessions. A guarded initialization loads one session; initialization is
  published only after tokenizer setup succeeds. Failed initialization can retry.
- An empty classifier batch tried to load weights and then failed concatenation.
  It now returns correctly shaped empty scores/predictions without loading files.
- Missing ONNX asset/dependency declarations could evade startup completeness
  checks. Neural artifacts must declare both inference assets and runtime versions;
  an incomplete artifact stays unavailable instead of advertising readiness.
- The body limiter appended an oversized chunk before checking its length.
  It now rejects that chunk before copying it into its bounded buffer.
- API documentation and the HTTP checker assumed API and model versions were
  identical. They are independent now; `/model` exposes both versions, language,
  labels and limits without inference or private training details.

## Validation

44 local tests passed, including regressions for malformed input, private value
redaction, missing metadata, concurrent first initialization and retry after failure.
Lint, formatting and installed dependency checks passed. Existing normal input,
artifact integrity and certificate rollback checks remain covered.

Server acceptance and CI evidence are recorded in [deployment.md](deployment.md)
and [deployment_verification.json](deployment_verification.json).
