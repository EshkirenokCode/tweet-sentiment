# Deployment checks

Verified 2026-10-30, model v1.1.0.

- [API and docs](https://tweet-sentiment.gulevskii.dev/docs); `/` redirects to docs.
- `/health`, `/ready`, `/docs`, `/openapi.json`, prediction: HTTP 200.
- Blank input, wrong type, excessive length: 422. Oversized body: 413.
- Four preprocessing regression cases agreed with the local pipeline.
- A 24-request probe returned 14 HTTP 200 and 10 HTTP 429 responses.
- Normal TLS verification was enabled. Certificate expires 2027-01-26.
- Model SHA-256 on the server:
  `29cc3e5ee08500693bc09c8f3d07de69ac1ec678431967d257fb170723fc42f1`.
- [CI](https://github.com/EshkirenokCode/tweet-sentiment/actions):
  30 tests, lint, Docker build/run and HTTP checks passed.

The API has a one-CPU/512-MiB limit; nginx ingress has 0.25 CPU/64 MiB. Observed
memory after startup was about 125 MiB and 5.6 MiB. Neither container publishes
host ports; the existing HTTPS edge connects through a dedicated Docker network.
The effective prediction quota is shared: 5 requests/second, burst 10.

Only this project's API container was recreated for v1.1; its nginx ingress was
reloaded to resolve the new upstream. Other container start times/restart counts
and existing application virtual-host checksums were unchanged. No corpus was
copied to the server.

Certificate renewal runs twice daily through `tweet-sentiment-certificate.timer`.
The timer is active. v1.1 restores the old certificate pair on nginx validation
or reload failure; both cases are covered by tests. The Docker Certbot client's
TLS handshake timed out even though host clients could reach ACME. Certbot now
runs in its own Python 3.12 environment with pinned dependencies. Reconfiguration
and a full staging renewal succeeded without changing TLS verification. The
installed service also exited successfully with its 256-MiB/half-CPU limits.
Only the systemd timer adds a random delay; Certbot's own delay is disabled.
Keys and ACME accounts stay
outside Git. Maintenance and rollback commands are in [deploy/README.md](../deploy/README.md).

External status evidence: [deployment_verification.json](deployment_verification.json).
