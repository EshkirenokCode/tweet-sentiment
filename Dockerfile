FROM python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    PORT=8000 MODEL_DIR=/app/artifacts
WORKDIR /app
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY src ./src
RUN pip install --no-cache-dir --no-deps . \
    && useradd --uid 1000 --create-home app
COPY artifacts ./artifacts
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/ready', timeout=3)"
CMD ["sh", "-c", "exec uvicorn tweet_sentiment.api:app --host 0.0.0.0 --port ${PORT} --workers 1 --limit-concurrency 16 --timeout-keep-alive 5 --no-access-log"]
