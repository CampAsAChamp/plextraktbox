import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The built SPA is emitted into the backend package's static/ dir so the single
// Docker image can serve it. In dev, /api is proxied to the uvicorn server.
// Vitest config lives in vitest.config.ts to keep the two type worlds separate.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../backend/plextraktbox/static",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
