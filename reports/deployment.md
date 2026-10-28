# Deployment status

Local API on 2026-10-28: `/health`, `/ready`, `/docs` and prediction/validation
requests verified against the evaluated artifact. Local loopback latency measured.

Docker is not installed on the development Mac. The Dockerfile and nginx/Compose
configuration are provided. GitHub CI builds and runs the API image and executes
HTTP smoke checks, without downloading the dataset or retraining. The actual CI
result must be checked after publication; configuration alone is not a passed build.

Public HTTPS API: pending a separate hosting environment/account. A local address
is not an externally usable API. No MAYAK configuration was accessed or modified.
