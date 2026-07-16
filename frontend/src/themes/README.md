# UI themes

Built-in palettes live as `createTheme()` modules in this directory. Custom themes are CSS
files under `{DATA_DIR}/themes/` (edit via Settings → Theme → **Custom CSS**, or mount a volume).

## Custom CSS format

Settings has one Custom CSS editor: paste, **Load example**, **Import file** (into the editor), then
**Save theme**. Saved customs appear in the theme picker with preview colors taken from
`--mantine-color-dark-9`, `--mantine-color-dark-7`/`-8`, and `--mantine-primary-color-filled`.

Start from [`example-theme.css`](./example-theme.css). Headers plus a `:root[data-ptb-theme="…"]`
block are required — `@id` becomes `{id}.css` on disk:

```css
/* @name: Harbor Dusk */
/* @id: harbor-dusk */
:root[data-ptb-theme="harbor-dusk"] {
  --mantine-color-dark-0: #e6f0f2;
  --mantine-color-dark-9: #0b1418;
  --mantine-primary-color-filled: #2dd4bf;
  --ptb-body-gradient: linear-gradient(165deg, #0b1418 0%, #111c21 42%, #18272d 100%);
}
```

Useful variables:

| Variable                                           | Role                            |
| -------------------------------------------------- | ------------------------------- |
| `--mantine-color-dark-0` … `-9`                    | Text → deepest surface          |
| `--mantine-primary-color-filled` / `-filled-hover` | Primary buttons & accents       |
| `--mantine-primary-color-light*`                   | Soft primary backgrounds        |
| `--mantine-primary-color-0` … `-9`                 | Full primary scale              |
| `--ptb-body-gradient`                              | Full-page background atmosphere |

- `@id` must be unique, lowercase, and not collide with built-ins (`cinema-night`,
  `one-dark-pro`, `nord`, `dracula`)
- Max file size: 64KB
- The SPA injects the stylesheet and sets `data-ptb-theme` on `<html>`
