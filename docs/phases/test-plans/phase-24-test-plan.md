# Phase 24 verification checklist

**Scope:** Selectable UI themes (built-ins + custom upload/volume) — see [phase-24.md](../phase-24.md).

**Prerequisites:** Phase 13 done (Settings + `setting` table). Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend -- tests/api/test_themes.py tests/unit/test_themes_service.py
mise run test-frontend -- src/themes/registry.test.ts src/api/themes.test.ts
mise run check       # CI parity before marking phase done
```

- [ ] Theme list API returns four built-ins; default `ui_theme` is `one-dark-pro`
- [ ] Upload / activate / delete custom theme; missing custom falls back to `one-dark-pro`
- [ ] Cannot delete or overwrite built-in ids; oversize CSS rejected
- [ ] Frontend registry exposes Atom One Dark Pro as default

## 2. Container / browser

```bash
mise run up          # or mise run dev-frontend + dev-backend
```

- [ ] Fresh install / cleared `ui_theme` loads **Atom One Dark Pro** (blue accent, `#282c34` surfaces)
- [ ] Settings → Theme: switch among One Dark Pro, Cinema Night, Nord, Dracula; chrome primary accent updates
- [ ] Refresh page — active theme persists
- [ ] Upload or paste a valid custom CSS theme; it appears in the grid; activating injects styles
- [ ] Delete custom theme; if it was active, UI falls back to One Dark Pro
- [ ] Optional: mount a host folder at `/data/themes` with a `.css` file; **Refresh themes** lists it

## 3. API smoke (optional)

```bash
mise run api-login   # writes cookies.txt — see testing.md
curl -s -b cookies.txt http://localhost:8000/api/themes | jq .
curl -s -b cookies.txt -X PUT -H 'Content-Type: application/json' -H 'X-Requested-With: XMLHttpRequest' \
  -d '{"theme_id":"nord"}' http://localhost:8000/api/settings/theme | jq .
```

## 4. Reset / fixtures

```bash
# Remove custom themes and reset active id (SQLite setting key ui_theme)
rm -rf data/themes
# Or delete rows / re-run ensure_defaults after wiping KEY_UI_THEME
```

## 5. Notes

- Custom format: `frontend/src/themes/README.md` and phase-24 custom CSS section
- Deploy volume example: [deploy/truenas.md](../../deploy/truenas.md)
