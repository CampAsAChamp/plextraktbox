---
paths:
  - frontend/**/*.ts
  - frontend/**/*.tsx
---

# Frontend (React / TypeScript)

- React 18 + Vite + TypeScript under `frontend/src/`
- UI: Mantine components; data fetching: TanStack Query
- Forms: zod + local state; helpers in `components/connections/connectionFormHelpers.ts`
- Prefer absolute `src/` imports (e.g. `import { x } from "api/client"`)
- CSS modules for component styles (`*.module.css`)
- Vitest + React Testing Library; specs live under `frontend/tests/` (mirrors `src/`), not co-located in `src/`
- Lint/format: ESLint + Prettier (`npm run lint`, `npm run format`) — included in `mise run lint` / `check`

## Dev

Vite dev server proxies API to backend :8000. Open http://localhost:5173 during native dev.

Run: `mise run test-frontend` or `cd frontend && npm run test`
