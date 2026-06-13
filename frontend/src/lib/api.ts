import { clearStoredSession } from './auth'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

export interface ApiError extends Error {
  /** 业务错误码（如 "400003" / "600002"），后端 ErrorCode enum 输出 */
  code?: string
  /** request_id（HTTP 链路追踪 ID，方便排查） */
  requestId?: string
  /** 兼容旧字段：路径不存在等真正的 HTTP 错误时 starlette 仍走 4xx，本字段保留 */
  status?: number
}

export interface ApiRequestOptions extends RequestInit {
  /** true 时 401/AUTH_ERROR 不自动登出/跳转 — 适合 /api/auth/login 等本身就在做认证的请求 */
  skipAuthRedirect?: boolean
}

interface ResponseEnvelope<T> {
  success: boolean
  code: string
  message: string
  detailMessage?: string | null
  data?: T | null
  request_id?: string | null
}

/** 业务错误码常量（与后端 src/common/response/response_code.py 同步）。 */
export const ERROR_CODES = {
  PARAM_ERROR: '400001',
  VALIDATION_ERROR: '400002',
  AUTH_ERROR: '400003',
  FORBIDDEN: '400004',
  NOT_FOUND: '400005',
  RATE_LIMIT: '400006',
  CONFLICT: '400009',
  SYS_ERROR: '500001',
  KILL_SWITCH_PAUSED: '600001',
  RISK_REJECTED: '600002',
} as const

/**
 * 处理认证失败：清掉本地 session, 跳到 /login?reason=session_expired.
 * 已在 /login 页时跳过 (避免登录页内部接口失败造成的循环跳转).
 */
function handleUnauthorized() {
  if (typeof window === 'undefined') return
  try {
    clearStoredSession()
  } catch {
    // localStorage 不可用时静默
  }
  const here = window.location.pathname
  if (!here.startsWith('/login')) {
    window.location.href = '/login?reason=session_expired'
  }
}

/**
 * Stage 4 重构后：所有业务异常都返 HTTP 200 + body `{success: false, code, message, request_id}`。
 * 成功响应：HTTP 200 + body `{success: true, code: "0", data: <真实数据>, request_id}`。
 *
 * apiRequest 自动解 envelope 并返 `data` 字段；业务错误抛 ApiError。
 * 真传输错误（路径不存在 / 网络断开）才会 HTTP 4xx/5xx，此时 `res.ok` 为 false。
 */
export async function apiRequest<T>(path: string, init?: ApiRequestOptions): Promise<T> {
  const { skipAuthRedirect, ...rest } = init || {}
  const res = await fetch(`${API_BASE}${path}`, {
    cache: 'no-store',
    ...rest,
    headers: {
      ...(rest.headers || {}),
    },
  })

  // 真传输错误（404 路径不存在 / 5xx 等 — 后端 handler 处理不到的）
  if (!res.ok) {
    const error = new Error(`HTTP ${res.status}`) as ApiError
    error.status = res.status
    if (res.status === 401 && !skipAuthRedirect) handleUnauthorized()
    throw error
  }

  // 解 envelope
  let body: ResponseEnvelope<T>
  try {
    body = (await res.json()) as ResponseEnvelope<T>
  } catch {
    const error = new Error('Invalid JSON response') as ApiError
    error.status = res.status
    throw error
  }

  // 业务异常：HTTP 200 + success: false
  if (body && typeof body === 'object' && body.success === false) {
    const error = new Error(body.message || 'Business error') as ApiError
    error.code = body.code
    error.requestId = body.request_id ?? undefined
    error.status = 200
    if (body.code === ERROR_CODES.AUTH_ERROR && !skipAuthRedirect) handleUnauthorized()
    throw error
  }

  // 成功 — 返 data 字段（兼容极旧接口直接返非 envelope 的情况）
  if (body && typeof body === 'object' && 'success' in body) {
    return (body.data as T) ?? (undefined as unknown as T)
  }
  return body as unknown as T
}

export function buildAuthHeaders(token?: string, hasBody?: boolean): HeadersInit {
  return {
    ...(hasBody ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export { API_BASE }


// ---- Commands API (Plan 3) ------------------------------------------------

export interface KillSwitchState {
  state: 'active' | 'paused'
}

export async function getKillSwitch(token: string): Promise<KillSwitchState> {
  return apiRequest<KillSwitchState>('/commands/kill-switch', {
    headers: buildAuthHeaders(token, false),
  })
}

export async function pauseKillSwitch(token: string, reason: string): Promise<KillSwitchState> {
  return apiRequest<KillSwitchState>('/commands/pause', {
    method: 'POST',
    headers: buildAuthHeaders(token, true),
    body: JSON.stringify({ reason }),
  })
}

export async function resumeKillSwitch(token: string, reason: string): Promise<KillSwitchState> {
  return apiRequest<KillSwitchState>('/commands/resume', {
    method: 'POST',
    headers: buildAuthHeaders(token, true),
    body: JSON.stringify({ reason }),
  })
}

export async function manualClosePosition(
  token: string, positionId: number, reason: string,
): Promise<{ position_id: number; trade_id: number; status: string }> {
  return apiRequest('/commands/close-position/' + positionId, {
    method: 'POST',
    headers: buildAuthHeaders(token, true),
    body: JSON.stringify({ reason }),
  })
}

export async function manualCloseAll(
  token: string, reason: string,
  accountId: number = 1, tradingMode: string = 'testnet',
): Promise<{ task_id: number; status: string }> {
  // close-all 已切异步入队 (spec §4.9.1): 立即返回 task_id, 结果走 GET /api/tasks/{id} 或 WS task.status_changed
  return apiRequest('/commands/close-all', {
    method: 'POST',
    headers: buildAuthHeaders(token, true),
    body: JSON.stringify({
      confirmation: 'CLOSE ALL',
      reason, account_id: accountId, trading_mode: tradingMode,
    }),
  })
}

export interface TaskStatus {
  id: number
  task_type: string
  status: string
  attempts: number
  enqueued_at: string | null
  started_at: string | null
  finished_at: string | null
  error_message: string | null
  trading_mode: string
}

export async function getTask(token: string, taskId: number): Promise<TaskStatus> {
  return apiRequest<TaskStatus>('/tasks/' + taskId, {
    headers: buildAuthHeaders(token, false),
  })
}

export async function resolveBreaker(
  token: string, eventId: number, reason: string,
): Promise<{ risk_event_id: number; resolved: boolean }> {
  return apiRequest('/commands/resolve-breaker/' + eventId, {
    method: 'POST',
    headers: buildAuthHeaders(token, true),
    body: JSON.stringify({ reason }),
  })
}
