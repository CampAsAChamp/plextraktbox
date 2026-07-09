"""Console entrypoint: ``media-sync`` runs the uvicorn server."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("MEDIA_SYNC_HOST", "0.0.0.0")  # noqa: S104 - self-hosted container
    port = int(os.getenv("MEDIA_SYNC_PORT", "8000"))
    uvicorn.run("media_sync.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
