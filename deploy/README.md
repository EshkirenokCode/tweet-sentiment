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

Replace that argument only with a real allocated endpoint. Check `/docs` in a browser
and record the date, endpoint and verification result in `reports/deployment.md`.
No public endpoint has been allocated as part of the initial local setup.
