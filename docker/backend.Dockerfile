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

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
