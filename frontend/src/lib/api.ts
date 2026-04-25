const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

export interface ApiError extends Error {
  status?: number
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

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    cache: 'no-store',
    ...init,
    headers: {
      ...(init?.headers || {}),
    },
  })

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
