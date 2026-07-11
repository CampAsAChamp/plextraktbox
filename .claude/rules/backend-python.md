---
paths:
  - backend/**/*.py
---

# Backend (Python / FastAPI)

- Python 3.14, `from __future__ import annotations`, type hints throughout
- Package: `plextraktbox` under `backend/plextraktbox/`
- SQLModel models + Alembic migrations in `backend/migrations/`
- structlog for logging; redact tokens/passwords before persist/stream
- Fernet-encrypt third-party tokens in `connection.secret_enc`
- API routes in `api/`; business logic in `services/`; HTTP clients in `clients/`

## Tests

- pytest + pytest-asyncio; HTTP mocking with respx
- Fakes in `backend/tests/fakes/` for Plex/Trakt/Letterboxd/TMDB
- Run: `mise run test-backend`

## Lint

ruff + mypy — included in `mise run check`.
