import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // 相对资源路径：同一构建产物可挂任意路径前缀（build-once / deploy-many）
  base: "./",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: mode === "real" ? 5174 : 5173,
    // 本地真后端联调：npm run dev:real（--mode real）
    // 同源转发（cookie/无 CORS），此时前端自动禁用 MSW（见 client.ts USE_MOCK）
    proxy:
      mode === "real"
        ? {
            "/api": {
              target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
              changeOrigin: true,
            },
            "/ws": {
              target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
              changeOrigin: true,
              ws: true,
            },
          }
        : undefined,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: false,
  },
}));
