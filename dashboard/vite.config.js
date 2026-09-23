import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the gateway runs separately on :8000; in production it serves dist/ itself.
const gateway = process.env.MESHAID_GATEWAY || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    proxy: {
      "/api": gateway,
      "/ws": { target: gateway.replace(/^http/, "ws"), ws: true },
    },
  },
});
