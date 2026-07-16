import path from "node:path"
import { fileURLToPath } from "node:url"

import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

const root = path.dirname(fileURLToPath(import.meta.url))

// Kept separate from vite.config.ts because vitest bundles its own (older) vite
// types; mixing the `test` key into the vite defineConfig trips a type mismatch.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      src: path.resolve(root, "src"),
      tests: path.resolve(root, "tests"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./tests/setup.ts",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
})
