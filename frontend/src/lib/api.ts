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
