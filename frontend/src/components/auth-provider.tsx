'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { apiRequest, buildAuthHeaders } from '@/lib/api'
import { AuthApiResponse, AuthApiUser, AuthSession, clearStoredSession, persistSession, readStoredSession, toAuthSession, updateSessionUser } from '@/lib/auth'

interface AuthContextValue {
  session: AuthSession | null
  ready: boolean
  login: (input: { email: string; password: string }) => Promise<AuthSession>
  register: (input: { name: string; email: string; password: string }) => Promise<AuthSession>
  logout: () => void
  refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function buildUsername(name: string, email: string) {
  const preferred = name.trim() || email.split('@')[0] || 'alphapilot-user'
  return preferred
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 32) || 'alphapilot-user'
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const stored = readStoredSession()
    setSession(stored)
    setReady(true)
  }, [])

  const refreshSession = async () => {
    const stored = readStoredSession()
    if (!stored?.token) {
      setSession(null)
      return
    }

    try {
      const user = await apiRequest<AuthApiUser>('/auth/me', {
        headers: buildAuthHeaders(stored.token),
      })
      const next = updateSessionUser(stored, user)
      persistSession(next)
      setSession(next)
    } catch {
      clearStoredSession()
      setSession(null)
    }
  }

  useEffect(() => {
    if (!ready) return
    void refreshSession()
  }, [ready])

  const value = useMemo<AuthContextValue>(() => ({
    session,
    ready,
    login: async ({ email, password }) => {
      const payload = await apiRequest<AuthApiResponse>('/auth/login', {
        method: 'POST',
        headers: buildAuthHeaders(undefined, true),
        body: JSON.stringify({ email, password }),
      })
      const next = toAuthSession(payload)
      persistSession(next)
      setSession(next)
      return next
    },
    register: async ({ name, email, password }) => {
      const payload = await apiRequest<AuthApiResponse>('/auth/register', {
        method: 'POST',
        headers: buildAuthHeaders(undefined, true),
        body: JSON.stringify({
          username: buildUsername(name, email),
          email,
          password,
        }),
      })
      const next = toAuthSession(payload)
      persistSession(next)
      setSession(next)
      return next
    },
    logout: () => {
      clearStoredSession()
      setSession(null)
    },
    refreshSession,
  }), [ready, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
