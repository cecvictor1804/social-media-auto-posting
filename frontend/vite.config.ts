import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Dev: Vite serves the SPA on :5173 and proxies API/OAuth/health to the
// FastAPI app on :8000 so the session cookie stays same-origin.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/oauth": "http://localhost:8000",
      "/healthz": "http://localhost:8000",
    },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
