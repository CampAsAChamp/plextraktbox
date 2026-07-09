# syntax=docker/dockerfile:1

# ---- Stage 1: build the React SPA ----
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
# Vite emits into ../backend/plextraktbox/static; redirect it to a build dir here.
RUN npm run build -- --outDir dist --emptyOutDir

# ---- Stage 2: python runtime ----
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLEXTRAKTBOX_ENV=prod \
    PLEXTRAKTBOX_DATA_DIR=/data

WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/plextraktbox ./plextraktbox
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./
RUN pip install --no-cache-dir .

# Bring in the built SPA
COPY --from=frontend /app/frontend/dist ./plextraktbox/static

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/data"]
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
