# Deployment checks

Verified 2026-11-04 (Asia/Bangkok): API 1.2.1, model 1.2.0.

- [API and docs](https://tweet-sentiment.gulevskii.dev/docs); `/` redirects to docs.
- `/health`, `/ready`, `/docs`, `/openapi.json`, `/model`, prediction: HTTP 200.
- Blank input, wrong type, excessive character/token length: 422. Oversized body: 413.
- Non-finite numbers, unpaired Unicode escapes and invalid Unicode field names: 422.
  Validation errors omit submitted values and exception context.
- A valid 245-word input succeeded; token overflow was rejected without truncation.
- Eight prediction responses matched the preceding production release exactly.
- A 24-request probe returned 17 HTTP 200 and 7 HTTP 429 responses.
- TLS verification was enabled. Certificate expires 2027-01-26.
- Pipeline and ONNX/tokenizer hashes match the unchanged committed model metadata.
- [CI for serving source](https://github.com/EshkirenokCode/tweet-sentiment/actions/runs/41693247635):
  44 tests, lint, Docker build/run and HTTP checks passed.

Before switching production, a temporary canary passed readiness, HTTP acceptance
and eight-response compatibility checks under the same one-CPU/512-MiB limit.
It was removed after the switch. API version 1.2.1 and model version 1.2.0 are
reported independently by `/model`. [Review and fixes](review-v1.2.1.md).

This release did not retrain or rescore the model. The model's Linux x86-64 test
accuracy of 69.68% and macro-F1 of 0.6928 were measured on 2026-10-30. Its validation
macro-F1 was 0.7018 versus 0.7048 on ARM; 52/2,000 predictions differed. Those checks
streamed inputs through SSH to a temporary process without persisting raw corpus
files on the server. [Platform check](experiments/server_parity.json),
[evaluation](evaluation.md).

The API retains one CPU/512 MiB; nginx ingress retains 0.25 CPU/64 MiB. Observed
memory after external acceptance was 156 MiB and 2.6 MiB. Neither container
publishes host ports; the existing HTTPS edge connects through a dedicated Docker
network. The effective prediction quota is shared: 5 requests/second, burst 10.

Only this project's API container was recreated. Its own nginx ingress was
reloaded to resolve the upstream. Other container start times/restart counts and
existing application virtual-host checksums were unchanged. The shared HTTPS
edge was not restarted or reconfigured for this update.

Certificate renewal runs twice daily through `tweet-sentiment-certificate.timer`.
The timer remains active, with the last service result successful. Renewal runs
in a separate Python 3.12 environment with pinned dependencies and restores the
old certificate pair on nginx validation or reload failure. Both failure paths
are tested. The service has a 256-MiB/half-CPU limit; only the timer adds jitter.
The staging renewal and installed service were verified during the preceding
certificate repair. Keys and ACME accounts remain outside Git.
[Maintenance and rollback](../deploy/README.md).

External status and server checks: [deployment_verification.json](deployment_verification.json).
