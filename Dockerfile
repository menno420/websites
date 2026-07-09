# Control-plane site (readiness board + journal browser).
# Railway: bind 0.0.0.0:$PORT; env vars documented in docs/site.md.
FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Deployed-commit SHA, baked at build time as a FALLBACK source for /version and
# the readiness board's deploy-state cell. Railway injects RAILWAY_GIT_COMMIT_SHA
# at runtime (the primary source), so this ARG is optional — pass it via Railway
# service build args (or `docker build --build-arg GIT_SHA=$(git rev-parse HEAD)`)
# for a local/non-Railway deploy. Unset → the app reports "unknown" honestly.
ARG GIT_SHA=""
ENV GIT_SHA=$GIT_SHA

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
