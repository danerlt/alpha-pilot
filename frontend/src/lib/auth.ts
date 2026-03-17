export type UserRole = 'user' | 'admin'
export type UserStatus = 'active' | 'disabled'

export interface SessionUser {
  id: number
  username: string
  name: string
  email: string
  role: UserRole
  status: UserStatus
}

export interface AuthSession {
  user: SessionUser
  token: string
  createdAt: string
}

export interface AuthApiUser {
  id: number
  username: string
  email: string
  role: UserRole
  status: UserStatus
}

export interface AuthApiResponse {
  access_token: string
  token_type: string
  user: AuthApiUser
}

export const AUTH_STORAGE_KEY = 'alpha-pilot-session'

function normalizeUser(user: AuthApiUser): SessionUser {
  return {
    id: user.id,
    username: user.username,
    name: user.username,
    email: user.email,
    role: user.role,
    status: user.status,
  }
}

export function toAuthSession(payload: AuthApiResponse): AuthSession {
  return {
    user: normalizeUser(payload.user),
    token: payload.access_token,
    createdAt: new Date().toISOString(),
  }
}

export function updateSessionUser(session: AuthSession, user: AuthApiUser): AuthSession {
  return {
    ...session,
    user: normalizeUser(user),
  }
}

export function readStoredSession(): AuthSession | null {
  if (typeof window === 'undefined') return null
  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw) as AuthSession
    if (!parsed?.user?.email || !parsed?.token) return null
    if (parsed.user.role !== 'admin' && parsed.user.role !== 'user') return null
    if (parsed.user.status !== 'active' && parsed.user.status !== 'disabled') return null
    if (typeof parsed.user.id !== 'number') return null
    return parsed
  } catch {
    return null
  }
}

export function persistSession(session: AuthSession) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function clearStoredSession() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(AUTH_STORAGE_KEY)
}
