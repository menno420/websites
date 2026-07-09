# Public bot site (server-rendered marketing + reference).
# Railway service: Root Directory = botsite (build context is this folder),
# so this Dockerfile sees botsite/'s contents at its build root. It binds
# 0.0.0.0:$PORT; env vars are documented in docs/botsite.md (none required — the
# public data feed is anonymous raw.githubusercontent.com).
FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service into a `botsite` package so `botsite.app:app` imports cleanly.
COPY . ./botsite

# Deployed-commit SHA, baked at build time as a FALLBACK source for /version.
# Railway injects RAILWAY_GIT_COMMIT_SHA at runtime (the primary source), so this
# ARG is optional; unset → /version reports "unknown" honestly.
ARG GIT_SHA=""
ENV GIT_SHA=$GIT_SHA

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh", "-c", "uvicorn botsite.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
