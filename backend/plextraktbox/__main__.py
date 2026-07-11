"""Console entrypoint: ``plextraktbox`` runs the uvicorn server."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")  # noqa: S104 - self-hosted container
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "plextraktbox.main:app",
        host=host,
        port=port,
        reload=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
