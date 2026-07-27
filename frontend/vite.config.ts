import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import path from "node:path";

const backendProxyUrl =
  process.env.CORPUS_BACKEND_PROXY_URL ?? "http://127.0.0.1:8099";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    dedupe: ["react", "react-dom"],
  },
  server: {
    proxy: {
      "/api": backendProxyUrl,
      "/healthz": backendProxyUrl,
      "/readyz": backendProxyUrl,
    },
  },
});
