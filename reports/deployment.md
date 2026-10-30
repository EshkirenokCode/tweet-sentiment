# Deployment checks

Verified 2026-10-30, model v1.2.0.

- [API and docs](https://tweet-sentiment.gulevskii.dev/docs); `/` redirects to docs.
- `/health`, `/ready`, `/docs`, `/openapi.json`, prediction: HTTP 200.
- Blank input, wrong type, excessive character/token length: 422. Oversized body: 413.
- A valid 245-word input succeeded; token overflow was rejected without truncation.
- Four preprocessing regression cases agreed with the development pipeline.
- A 24-request probe returned 15 HTTP 200 and 9 HTTP 429 responses.
- TLS verification was enabled. Certificate expires 2027-01-26.
- Pipeline and both ONNX/tokenizer asset hashes match committed metadata.
- [CI for serving source](https://github.com/EshkirenokCode/tweet-sentiment/actions/runs/41039295247):
  33 tests, lint, Docker build/run and HTTP checks passed.

Before switching production, a temporary canary passed readiness and prediction
checks under the same one-CPU/512-MiB limit. Full validation and test inputs were
streamed over SSH to its process; raw corpus files were not persisted on the server.
The canary was removed after the production switch.

Linux x86-64 int8 validation macro-F1 was 0.7018 versus 0.7048 on the development
ARM machine; 52/2,000 predictions differed. The same weights, checkpoint and
precision were retained. Headline test metrics use the serving architecture:
accuracy 69.68%, macro-F1 0.6928. ARM measurements are preserved separately.
See [platform check](experiments/server_parity.json) and [evaluation](evaluation.md).

The API retains one CPU/512 MiB; nginx ingress retains 0.25 CPU/64 MiB. Observed
memory after external acceptance was 153.3 MiB and 5.6 MiB. Neither container
publishes host ports; the existing HTTPS edge connects through a dedicated Docker
network. The effective prediction quota is shared: 5 requests/second, burst 10.

Only this project's API container was recreated. Its own nginx ingress was
reloaded to resolve the upstream. Other container start times/restart counts and
existing application virtual-host checksums were unchanged. The shared HTTPS
edge was not restarted or reconfigured for this model update.

Certificate renewal runs twice daily through `tweet-sentiment-certificate.timer`.
The timer remains active, with the last service result successful. Renewal runs
in a separate Python 3.12 environment with pinned dependencies and restores the
old certificate pair on nginx validation or reload failure. Both failure paths
are tested. The service has a 256-MiB/half-CPU limit; only the timer adds jitter.
The staging renewal and installed service were verified during the preceding
certificate repair. Keys and ACME accounts remain outside Git.
[Maintenance and rollback](../deploy/README.md).

External status and server checks: [deployment_verification.json](deployment_verification.json).
