import { clearStoredSession } from './auth'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

export interface ApiError extends Error {
  status?: number
}

export interface ApiRequestOptions extends RequestInit {
  /** true 时 401 不自动登出/跳转 — 适合 /api/auth/login 等本身就在做认证的请求 */
  skipAuthRedirect?: boolean
}

async function parseError(res: Response): Promise<ApiError> {
  let message = `HTTP ${res.status}`
  try {
    const data = await res.json()
    if (typeof data?.detail === 'string') message = data.detail
  } catch {
    // ignore json parse errors
  }
  const error = new Error(message) as ApiError
  error.status = res.status
  return error
}

/**
 * 处理 401: 清掉本地 session, 跳到 /login?reason=session_expired.
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

export async function apiRequest<T>(path: string, init?: ApiRequestOptions): Promise<T> {
  const { skipAuthRedirect, ...rest } = init || {}
  const res = await fetch(`${API_BASE}${path}`, {
    cache: 'no-store',
    ...rest,
    headers: {
      ...(rest.headers || {}),
    },
  })

  if (res.status === 401 && !skipAuthRedirect) {
    handleUnauthorized()
  }
  if (!res.ok) throw await parseError(res)
  return res.json()
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
): Promise<{ closed_position_ids: number[] }> {
  return apiRequest('/commands/close-all', {
    method: 'POST',
    headers: buildAuthHeaders(token, true),
    body: JSON.stringify({
      confirmation: 'CLOSE ALL',
      reason, account_id: accountId, trading_mode: tradingMode,
    }),
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
