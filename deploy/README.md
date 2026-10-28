# Deployment

The image includes the evaluated artifact; startup never downloads data or trains.
Use a separate host or managed Docker service. No existing MAYAK services are needed.

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
The existing edge proxy is attached only to that edge network and uses the
separate `public-proxy.conf` virtual host for this domain. Existing application
virtual-host files remain unchanged. Only a graceful edge reload is needed.
The inner nginx limits prediction requests to 5/second with a burst of 10;
behind the edge proxy this is an effective shared limit, not a per-visitor quota.

```bash
docker network create tweet-sentiment-edge
docker compose -f deploy/compose.server.yaml up -d --build
docker network connect tweet-sentiment-edge "$PROXY_CONTAINER"
```

Create the domain A record pointing to the server. Issue the initial certificate
using Certbot 5.8.0 (pinned image digest in `renew-certificate.sh`), `certonly
--webroot -w /acme --cert-name tweet-sentiment -d YOUR_DOMAIN`, with the existing
edge's ACME webroot mounted at `/acme` and this service's private certificate
directory at `/etc/letsencrypt`. Validate against staging first. No existing
listener has to stop. Copy the initial fullchain/key to the directory configured
as `CERT_DEST` before installing `public-proxy.conf`. Update that file's domain
and certificate paths if deploying elsewhere. Run `nginx -t` before reloading.

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

The timer checks twice daily. The renewal script uses a lock, updates only this
service's certificate, checks nginx configuration, and gracefully reloads the edge
only when the certificate changes. The previous certificate pair is retained for
rollback. A simulated renewal was verified after deployment.

If the existing edge container is recreated by its own deployment tooling, reconnect
it to `tweet-sentiment-edge`; Docker preserves the attachment across ordinary
container/daemon restarts, but not recreation. This manually managed virtual host
is stored separately from the proxy manager's numeric generated host files.

To roll back this service, remove only its virtual-host file, check/reload nginx,
disconnect the edge from `tweet-sentiment-edge`, stop this Compose project and
disable `tweet-sentiment-certificate.timer`. Leave other projects and their networks
alone. Keep the certificate backup if recovery is needed.
