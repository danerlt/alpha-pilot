/**
 * HTTP 客户端 —— VITE_API_BASE_URL 未配置时全站走 mock（USE_MOCK=true），
 * 配置后所有 service 无缝切换到真实后端（契约见 handoff/03）。
 */

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export const USE_MOCK = BASE === "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, body || res.statusText);
  }
  return (await res.json()) as T;
}

/** mock 模式的模拟网络延迟，让 loading 态可见可调 */
export function delay<T>(value: T, ms = 160): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}
