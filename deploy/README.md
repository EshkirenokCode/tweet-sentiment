# Deployment

The image includes the evaluated artifact; startup never downloads data or trains.
Use an isolated Compose project or a managed Docker service.

```bash
docker build -t tweet-sentiment .
docker run --rm --cpus=1 --memory=512m -p 127.0.0.1:8000:8000 tweet-sentiment
python scripts/http_smoke.py --url http://127.0.0.1:8000
```

`PORT` defaults to 8000 and can be set by the hosting service. Run one worker,
one CPU thread, 512 MiB memory, and retain the concurrency limit of 16. Use `/ready`
for health checks. The application buffers at most 8192 request-body bytes, including
chunked requests, and limits text to 2000 characters. It never logs prediction text.

`docker compose up --build -d` adds nginx at `127.0.0.1:8080`, with 8 KiB ingress
body limit and 5 prediction requests/second/IP (burst 10; HTTP 429). This binds only
to loopback. To publish, put a managed HTTPS ingress in front of it and configure
the real domain and certificate in that separate environment. If a managed service
runs just the API image, configure equivalent rate limits at its edge. Concurrency
limits alone are not a request-rate limit.

External acceptance:

```bash
python scripts/http_smoke.py --url https://YOUR-ACTUAL-HOST
```

The deployed endpoint is `https://tweet-sentiment.gulevskii.dev`.
Its external HTTP checks are recorded in `reports/deployment_verification.json`.

## Current server deployment

Source checkout: `/opt/tweet-sentiment/app`. `compose.server.yaml` runs the API
on an internal Docker network, with nginx ingress on a separate
`tweet-sentiment-edge` network. No application ports are published on the host.
For this project, the existing edge proxy joins the edge network, not the internal
API network. It uses a separate `public-proxy.conf` virtual host. Existing application
virtual-host files remain unchanged. Only a graceful edge reload is needed.
The inner nginx limits prediction requests to 5/second with a burst of 10;
behind the edge proxy this is an effective shared limit, not a per-visitor quota.

```bash
docker network create tweet-sentiment-edge
docker compose -f deploy/compose.server.yaml up -d --build
docker network connect tweet-sentiment-edge "$PROXY_CONTAINER"
```

Create the domain A record pointing to the server. Certbot runs in a separate
Python 3.12 environment, outside the API image:

```bash
python3.12 -m venv /opt/tweet-sentiment/certbot-venv
/opt/tweet-sentiment/certbot-venv/bin/python -m pip install -r deploy/certbot-requirements.lock
```

Creating the environment requires venv/ensurepip support. Without ensurepip, use
`venv --without-pip` and bootstrap pip from its official PyPI wheel inside that
environment; do not install Certbot into the system Python.

Issue the initial certificate with `certonly --webroot -w "$ACME_WEBROOT"
--cert-name tweet-sentiment -d YOUR_DOMAIN`, using `--config-dir
/opt/tweet-sentiment/tls`, `--work-dir /opt/tweet-sentiment/certbot-work`, and
`--logs-dir /opt/tweet-sentiment/certbot-logs`. Validate against staging first.
Copy the initial fullchain/key to `CERT_DEST` before installing `public-proxy.conf`.
Update that file's domain and certificate paths for another deployment.
Run `nginx -t` before reloading; no existing listener needs to stop.

Copy `host.env.example` to `/opt/tweet-sentiment/host.env`, set the three actual
host paths/container name, and keep it root-owned with mode 600. Certificate keys
and accounts are stored outside the checkout; they are never committed.

```bash
sudo install -m 644 deploy/tweet-sentiment-certificate.service /etc/systemd/system/
sudo install -m 644 deploy/tweet-sentiment-certificate.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo /opt/tweet-sentiment/app/deploy/renew-certificate.sh --dry-run
sudo systemctl enable --now tweet-sentiment-certificate.timer
```

The timer checks twice daily. The renewal script uses a lock and updates only this
service's certificate. It checks nginx configuration before reloading the edge.
If validation or reload fails, it restores the previous pair and exits with an error
so the next run retries. Regression tests cover both failure paths.
The oneshot service is limited to 256 MiB and half a CPU. The native environment
replaces the Certbot container, whose TLS connection to ACME timed out on this host.
Certificate verification remains enabled. Certbot's extra random delay is disabled:
the systemd timer already adds jitter, and its service has a five-minute timeout.
When migrating a Docker-issued certificate,
back up its renewal file, change its absolute certificate paths to the host paths,
then run `certbot reconfigure --cert-name tweet-sentiment --webroot -w "$ACME_WEBROOT"`
with the same config/work/log directories. This validates and saves the host webroot.

If the existing edge container is recreated by its own deployment tooling, reconnect
it to `tweet-sentiment-edge`; Docker preserves the attachment across ordinary
container/daemon restarts, but not recreation. This manually managed virtual host
is stored separately from the proxy manager's numeric generated host files.

To roll back this service, remove only its virtual-host file, check/reload nginx,
disconnect the edge from `tweet-sentiment-edge`, stop this Compose project and
disable `tweet-sentiment-certificate.timer`. Leave other projects and their networks
alone. Keep the certificate backup if recovery is needed.
