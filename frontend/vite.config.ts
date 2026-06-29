import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://gateway:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://notification-service:8008",
        ws: true,
      },
    },
  },
});
