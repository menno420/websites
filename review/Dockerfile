# Program review service (public, server-rendered, network-free at runtime).
# Railway service: Root Directory = review (build context is this folder), so
# this Dockerfile sees review/'s contents at its build root — including the
# committed data/snapshot.json the pages render from. Binds 0.0.0.0:$PORT.
FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service into a `review` package so `review.app:app` imports cleanly.
COPY . ./review

# Deployed-commit SHA, baked at build time as a FALLBACK source for /version.
# Railway injects RAILWAY_GIT_COMMIT_SHA at runtime (the primary source), so
# this ARG is optional; unset → /version reports "unknown" honestly.
ARG GIT_SHA=""
ENV GIT_SHA=$GIT_SHA

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh", "-c", "uvicorn review.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
