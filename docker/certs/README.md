# Corporate TLS CA (Zscaler)

`zscaler-root-ca.pem` is for **developer machines behind Zscaler** (or similar TLS inspection).
It is **not** required on TrueNAS or in the published GHCR image.

| Context | Behavior |
| ------- | -------- |
| GHCR / CI prod build | `USE_CORPORATE_CA=0` (default) — build and runtime use public CAs |
| Local prod image build on a corporate laptop | `USE_CORPORATE_CA=1` — trust this CA **during** `npm`/`pip` only; removed from the final image |
| Dev compose images (`docker/Dockerfile.dev-*`) | Always include the CA so `mise run up-dev` works on the corporate laptop |

```bash
# Local prod build behind Zscaler
USE_CORPORATE_CA=1 mise run build
# or
podman compose build --build-arg USE_CORPORATE_CA=1
```

At runtime, leave `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` unset unless you intentionally mount a
custom CA. See `backend/plextraktbox/ssl_compat.py` for Python 3.13+ strict-verify behavior when a
custom bundle is configured.
