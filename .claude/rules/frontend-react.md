---
paths:
  - frontend/**/*.ts
  - frontend/**/*.tsx
---

# Frontend (React / TypeScript)

- React 18 + Vite + TypeScript under `frontend/src/`
- UI: Mantine components; data fetching: TanStack Query
- Forms: react-hook-form + zod
- CSS modules for component styles (`*.module.css`)
- Vitest + React Testing Library for unit tests

## Dev

Vite dev server proxies API to backend :8000. Open http://localhost:5173 during native dev.

Run: `mise run test-frontend`
