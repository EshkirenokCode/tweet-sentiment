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
The optional nginx/Compose stack is configured but has not been executed;
the checked Docker run used the API image directly.

Public HTTPS API: pending a separate hosting environment/account. A local address
is not an externally usable API. No MAYAK configuration was accessed or modified.
