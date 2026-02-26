import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "streamator-react": path.resolve("../react/src/index.js"),
      "streamator-react/log.css": path.resolve("../react/src/log.css"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://3.89.183.234",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
