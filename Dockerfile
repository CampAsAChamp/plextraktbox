# ---- Stage 1: build the React SPA ----
FROM node:24-alpine AS frontend
# Trust Zscaler (and similar TLS-inspecting proxies) so npm can reach the registry.
COPY docker/certs/zscaler-root-ca.pem /etc/ssl/certs/zscaler-root-ca.pem
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/zscaler-root-ca.pem
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
# Vite emits into ../backend/plextraktbox/static; redirect it to a build dir here.
RUN npm run build -- --outDir dist --emptyOutDir

# ---- Stage 2: python runtime ----
FROM python:3.14-slim AS runtime
ARG GIT_SHA=
ARG BUILD_TIME=
COPY docker/certs/zscaler-root-ca.pem /etc/ssl/certs/zscaler-root-ca.pem
ENV SSL_CERT_FILE=/etc/ssl/certs/zscaler-root-ca.pem \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/zscaler-root-ca.pem \
    PIP_CERT=/etc/ssl/certs/zscaler-root-ca.pem \
    PLEXTRAKTBOX_GIT_SHA=${GIT_SHA} \
    PLEXTRAKTBOX_BUILD_TIME=${BUILD_TIME}
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=prod \
    DATA_DIR=/data

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
