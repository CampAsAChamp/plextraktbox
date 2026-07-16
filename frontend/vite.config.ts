import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { createColoredViteLogger } from "./src/lib/viteLogger";

const root = path.dirname(fileURLToPath(import.meta.url));

// The built SPA is emitted into the backend package's static/ dir so the single
// Docker image can serve it. In dev, /api is proxied to the uvicorn server.
// Vitest config lives in vitest.config.ts to keep the two type worlds separate.
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8000";
// docker-compose.dev.yml sets VITE_API_PROXY_TARGET; bind mounts on macOS/Podman
// often miss fs events, so poll for changes inside the frontend container.
const containerDev = Boolean(process.env.VITE_API_PROXY_TARGET);

export default defineConfig({
  customLogger: createColoredViteLogger(),
  plugins: [react()],
  resolve: {
    alias: {
      src: path.resolve(root, "src"),
    },
  },
  build: {
    outDir: "../backend/plextraktbox/static",
    emptyOutDir: true,
  },
  server: {
    host: true,
    port: 5173,
    watch: containerDev
      ? {
          usePolling: true,
          interval: 1000,
        }
      : undefined,
    hmr: containerDev
      ? {
          clientPort: 5173,
        }
      : undefined,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
