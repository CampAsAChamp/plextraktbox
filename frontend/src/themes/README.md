# UI themes (Phase 24)

Built-in palettes live as `createTheme()` modules in this directory. Custom themes are CSS
files under `{DATA_DIR}/themes/` (upload via Settings or mount a volume).

## Custom CSS format

```css
/* @name: My Theme */
/* @id: my-theme */
:root[data-ptb-theme="my-theme"] {
  --mantine-color-dark-0: #abb2bf;
  --mantine-color-dark-9: #1b1f25;
  --ptb-body-gradient: linear-gradient(165deg, #1b1f25 0%, #282c34 100%);
}
```

- `@id` must be unique, lowercase, and not collide with built-ins (`one-dark-pro`,
  `cinema-night`, `nord`, `dracula`)
- Max file size: 64KB
- The SPA injects the stylesheet and sets `data-ptb-theme` on `<html>`
