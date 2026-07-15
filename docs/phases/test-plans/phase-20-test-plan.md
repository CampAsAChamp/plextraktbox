# Phase 20 verification checklist

**Scope:** Mobile & responsive layout for the full SPA — see [phase-20.md](../phase-20.md).

**Prerequisites:** Phase 14 done (ops views). Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test        # includes frontend/src/components/layout/AppLayout.test.tsx
mise run check       # CI parity before marking phase done
```

- [ ] AppLayout burger opens the nav drawer and navigation works
- [ ] Frontend typecheck / vitest / lint pass via `mise run check`

## 2. Browser — device widths

```bash
mise run up          # or mise run dev-frontend + dev-backend
```

Use DevTools device emulation (or a real phone) at **~390px** and **~768px**:

- [ ] **Header:** no horizontal page scroll; health badge compact on narrow; account/notifications usable
- [ ] **Nav:** hamburger opens drawer; Escape / navigate closes it; desktop links remain at `sm+`
- [ ] **Login / setup:** full-width card, comfortable padding, no clip
- [ ] **Dashboard / Jobs / Runs:** tables scroll horizontally if needed; secondary columns hidden below `sm`; row actions via labeled menu (not tooltip-only icons)
- [ ] **Run detail + logs:** header actions wrap; log toolbar stacks / full-width filters; virtualized log pane still scrolls
- [ ] **Connections:** stepper vertical on narrow; Save / Test / Clear wrap
- [ ] **Job create/edit:** schedule presets grid; switches stacked
- [ ] **Settings:** mobile “Jump to section” Select; sticky TOC only at `sm+`; segmented controls fit

## 3. Touch & a11y smoke

- [ ] Primary chrome controls (burger, bell, account, row action menus) feel ≥ ~44px
- [ ] No hover-only row actions on Jobs / Dashboard
- [ ] Focused text inputs on iOS do not unexpected-zoom (16px base on narrow viewports)
- [ ] Notches / home indicator: header and bottom content clear of safe areas (`viewport-fit=cover`)

## 4. Reset / fixtures

No special DB state. Any account with jobs/runs exercises list pages; an open run exercises LogViewer.

## 5. Notes

- Breakpoint strategy: Mantine defaults (`sm` ≈ 768px). Prefer `visibleFrom` / `hiddenFrom` and `SimpleGrid` cols over ad-hoc media queries.
- No API or sync behavior changes in this phase.
