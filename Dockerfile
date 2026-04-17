# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend-builder
WORKDIR /app/app/frontend
COPY app/frontend/package.json app/frontend/package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY app/frontend/ ./
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Upgrade pip in its own cached layer.
RUN pip install --upgrade pip

# Copy both pyproject.toml AND the backend sources before `pip install .` —
# setuptools is configured with `[tool.setuptools.packages.find] where =
# ["app/backend"]`, so the directory must exist at install time. Keeping
# the backend sources in a dedicated COPY still provides good layer caching
# (requirements change less often than source files would).
COPY pyproject.toml ./
COPY app/backend ./app/backend
RUN pip install .

COPY --from=frontend-builder /app/app/frontend/dist ./app/frontend/dist
COPY scripts/start.sh ./scripts/start.sh
RUN chmod +x scripts/start.sh

# Create the unprivileged user after files are copied, then hand it
# ownership of /app so the app can read its own files under USER appuser.
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# Healthcheck uses /api/health/ready which does NOT contact external sources,
# so probes don't generate outbound traffic and can't be rate-limited upstream.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request;port=os.environ.get('PORT','7860');urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health/ready', timeout=3).read()"

CMD ["./scripts/start.sh"]
