# Deployment status

Local API on 2026-10-28: `/health`, `/ready`, `/docs` and prediction/validation
requests verified against the evaluated artifact. Local loopback latency measured.

Docker is not installed on the development Mac. The API image was built and run
successfully on the GitHub Actions Linux runner on 2026-10-28, with one CPU and
512 MiB memory. Lint, all 25 tests and HTTP smoke checks passed, including `/docs`,
readiness, prediction, invalid input and oversized bodies. No dataset download or
retraining was performed in CI.

Verified code commit: `7ada4c59d20581c68bfc19330eeb5d5f67e09783`.
[Successful CI run](https://github.com/EshkirenokCode/tweet-sentiment/actions/runs/40668808889).
That CI run checked the API image directly. The server Compose stack and nginx
ingress were subsequently started and verified on the hosting server.

## Public API, verified 2026-10-28

- Base URL: https://tweet-sentiment.gulevskii.dev
- Interactive docs: https://tweet-sentiment.gulevskii.dev/docs
- DNS: A record created through the owner's Porkbun browser session; other records
  retained. Public resolver returned the intended hosting IP.
- TLS: trusted Let's Encrypt certificate for this exact hostname, valid through
  2027-01-26; normal certificate verification was enabled during external checks.
- Model SHA-256 on the server:
  `2f0278b7a3b346cc2da6f096d2321e14a775fd20d589ac199edbe43643e68a2f`.
- `/health`, `/ready`, `/docs`, `/openapi.json` and `POST /predict`: HTTP 200.
- Blank input, wrong type and excessive text length: HTTP 422; oversized body: 413.
- Probe of 24 requests (at most 16 concurrent clients): 12 HTTP 200, 12 HTTP 429.
  The proxy enforces 5 predictions/second with burst 10; behind the edge this is
  an effective shared quota. HTTP redirects to HTTPS.
- Verified from the developer Mac outside the hosting server and in Chrome's
  interactive documentation. Raw status evidence: [deployment_verification.json](deployment_verification.json).
- API container: one CPU, 512 MiB; ingress: 0.25 CPU, 64 MiB. Observed idle memory
  after startup was about 152 MiB and 2.6 MiB respectively. These are observations,
  not load-capacity guarantees. No corpus was copied to the server.

Source and service files live under `/opt/tweet-sentiment`. The API uses an internal
Docker network and publishes no host ports. A separate virtual-host file and edge
network connect it to the existing HTTPS proxy. Existing application virtual-host
checksums, container start times and restart counts were verified unchanged.
Only the shared edge received a graceful configuration reload; existing application
containers were not restarted. No database or existing application configuration
was changed.

Certificate renewal: `tweet-sentiment-certificate.timer` is enabled with twice-daily
checks. A full `renew --dry-run` succeeded; the installed oneshot service also exited
successfully. Renewal updates only this service's certificate and reloads the edge
after validating nginx configuration. Keys and renewal accounts remain outside Git.
See [deployment maintenance](../deploy/README.md) for restart/recreation and rollback notes.
