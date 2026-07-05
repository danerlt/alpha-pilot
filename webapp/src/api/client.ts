/**
 * HTTP 客户端 —— 与后端统一响应包（src/common/response/response_schema.py）严格对齐：
 * `{success, code, message, detailMessage?, data, request_id}`，业务异常 HTTP 200 + success:false。
 * VITE_API_BASE_URL 未配置时启用 MSW（网络层 mock），业务代码路径与生产完全一致。
 */

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export const USE_MOCK = BASE === "";

export interface ApiEnvelope<T> {
  success: boolean;
  code: string;
  message: string;
  detailMessage?: string | null;
  data: T | null;
  request_id?: string | null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
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
  const body: unknown = await res.json();
  if (
    body !== null &&
    typeof body === "object" &&
    "success" in body &&
    "code" in body
  ) {
    const env = body as ApiEnvelope<T>;
    if (!env.success) {
      throw new ApiError(res.status, env.message, env.code);
    }
    return env.data as T;
  }
  // 未包装端点（如部分基础设施路由）原样返回
  return body as T;
}
