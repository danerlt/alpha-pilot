/**
 * 运行时配置 —— build-once / deploy-many：
 * 同一构建产物在容器启动时由 entrypoint 渲染 /config.js（window.__AP_CONFIG__）注入环境差异；
 * 本地 dev 无 config.js 值（public/config.js 为空对象）→ 回退 VITE_ 变量 → 默认 mock。
 */

export interface RuntimeConfig {
  /** API 前缀（如 "/ap-dev" 或 "https://host"），空 → mock 模式 */
  apiBaseUrl?: string;
  /** WS 完整地址；缺省由 apiBaseUrl 推导 */
  wsUrl?: string;
  /** SPA 挂载路径前缀（React Router basename），如 "/ap-dev-next" */
  basePath?: string;
}

declare global {
  interface Window {
    __AP_CONFIG__?: RuntimeConfig;
  }
}

const runtime: RuntimeConfig =
  typeof window !== "undefined" ? (window.__AP_CONFIG__ ?? {}) : {};

export const config = {
  apiBaseUrl:
    runtime.apiBaseUrl ??
    ((import.meta.env.VITE_API_BASE_URL as string | undefined) || ""),
  wsUrl: runtime.wsUrl ?? ((import.meta.env.VITE_WS_URL as string | undefined) || ""),
  basePath: runtime.basePath ?? "/",
};

/** 推导 WS 地址：支持绝对 http(s) 前缀与路径前缀（经反代）两种形态 */
export function resolveWsUrl(): string {
  if (config.wsUrl) return config.wsUrl;
  const base = config.apiBaseUrl;
  if (/^https?:\/\//.test(base)) {
    return base.replace(/^http/, "ws") + "/ws";
  }
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}${base}/ws`;
}
