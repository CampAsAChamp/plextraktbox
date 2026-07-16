# ---- Stage 1: build the React SPA ----
FROM node:24-alpine AS frontend
# Optional: trust Zscaler (or similar) during npm on corporate networks.
# Default 0 so CI / public builds use the normal CA store. Laptop:
#   podman compose build --build-arg USE_CORPORATE_CA=1
#   or set USE_CORPORATE_CA=1 in .env
ARG USE_CORPORATE_CA=0
WORKDIR /app/frontend
COPY docker/certs/zscaler-root-ca.pem /tmp/zscaler-root-ca.pem
# CVE-2026-12151: node:24-alpine ships undici 6.26.0 inside npm; replace with 6.27.0+.
RUN if [ "$USE_CORPORATE_CA" = "1" ]; then export NODE_EXTRA_CA_CERTS=/tmp/zscaler-root-ca.pem; fi; \
    cd /tmp \
    && npm pack undici@6.27.0 \
    && rm -rf /usr/local/lib/node_modules/npm/node_modules/undici \
    && mkdir -p /usr/local/lib/node_modules/npm/node_modules/undici \
    && tar -xzf undici-6.27.0.tgz -C /usr/local/lib/node_modules/npm/node_modules/undici --strip-components=1 \
    && rm -f undici-6.27.0.tgz
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ "$USE_CORPORATE_CA" = "1" ]; then export NODE_EXTRA_CA_CERTS=/tmp/zscaler-root-ca.pem; fi; \
    npm ci
COPY frontend/ ./
# Vite emits into ../backend/plextraktbox/static; redirect it to a build dir here.
RUN if [ "$USE_CORPORATE_CA" = "1" ]; then export NODE_EXTRA_CA_CERTS=/tmp/zscaler-root-ca.pem; fi; \
    npm run build -- --outDir dist --emptyOutDir

# ---- Stage 2: python runtime ----
# alpine: Debian slim currently ships unfixed HIGH/CRITICAL CVEs (perl/ncurses/etc.).
FROM python:3.14-alpine AS runtime
ARG GIT_SHA=
ARG BUILD_TIME=
ARG USE_CORPORATE_CA=0
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=prod \
    DATA_DIR=/data \
    PLEXTRAKTBOX_GIT_SHA=${GIT_SHA} \
    PLEXTRAKTBOX_BUILD_TIME=${BUILD_TIME}

# bash/shadow: entrypoint user management. su-exec: drop to PUID/PGID (TrueNAS ZFS mounts).
# Corporate CA is used only for apk/pip when USE_CORPORATE_CA=1, then removed from the trust store.
COPY docker/certs/zscaler-root-ca.pem /tmp/zscaler-root-ca.pem
RUN if [ "$USE_CORPORATE_CA" = "1" ]; then \
      cp /etc/ssl/certs/ca-certificates.crt /tmp/ca-backup.crt \
      && cat /tmp/zscaler-root-ca.pem >> /etc/ssl/certs/ca-certificates.crt; \
    fi \
    && apk add --no-cache bash shadow su-exec \
    && if [ "$USE_CORPORATE_CA" = "1" ]; then \
         mv /tmp/ca-backup.crt /etc/ssl/certs/ca-certificates.crt; \
       fi \
    && su-exec nobody true

WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/plextraktbox ./plextraktbox
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./
# Corporate CA is used only for this pip install when USE_CORPORATE_CA=1, then deleted.
# The published runtime image must not ship SSL_CERT_FILE / PIP_CERT pointing at Zscaler.
RUN if [ "$USE_CORPORATE_CA" = "1" ]; then \
      export SSL_CERT_FILE=/tmp/zscaler-root-ca.pem \
             REQUESTS_CA_BUNDLE=/tmp/zscaler-root-ca.pem \
             PIP_CERT=/tmp/zscaler-root-ca.pem; \
    fi; \
    pip install --no-cache-dir .; \
    rm -f /tmp/zscaler-root-ca.pem

# Bring in the built SPA
COPY --from=frontend /app/frontend/dist ./plextraktbox/static

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/data"]
# Default listen port; override at runtime with PORT (see docker-compose.yml / entrypoint).
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
