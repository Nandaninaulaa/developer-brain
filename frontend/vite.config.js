import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/static/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward API calls to the FastAPI backend during local dev.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
