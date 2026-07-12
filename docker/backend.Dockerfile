# Build context is the repo root (see docker-compose.yml) so this can COPY
# both backend/ and reference docs/ paths consistently with local dev.

FROM python:3.11-slim

WORKDIR /app

# PyMuPDF and faiss-cpu ship manylinux wheels for this base image, so no
# compiler toolchain is needed here — keeping the image lean matters more
# than shaving install time on a build step that only runs on dependency
# changes.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app

RUN pip install --no-cache-dir .

COPY backend/scripts ./scripts
COPY backend/data ./data

ENV PYTHONUNBUFFERED=1

# Runs as a non-root user in every environment, not just AWS/production — least privilege by
# default rather than an opt-in hardening step. /app/data is chowned here, before it ever
# becomes a volume mount point, specifically because Docker seeds a fresh named volume (or EFS
# access point, in the ECS deployment — see docs/aws-deployment.md) from the image directory's
# existing content *and ownership* on first mount; chowning after the fact wouldn't reach data
# written into the volume afterward.
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
