import { beforeEach, describe, expect, it } from 'vitest'
import {
  AUTH_STORAGE_KEY,
  clearStoredSession,
  persistSession,
  readStoredSession,
  toAuthSession,
  updateSessionUser,
  type AuthApiResponse,
  type AuthSession,
} from './auth'

const API_PAYLOAD: AuthApiResponse = {
  access_token: 'jwt-token',
  token_type: 'bearer',
  user: { id: 7, username: 'alice', email: 'alice@example.com', role: 'admin', status: 'active' },
}

describe('toAuthSession', () => {
  it('maps API payload to session with normalized user', () => {
    const s = toAuthSession(API_PAYLOAD)
    expect(s.token).toBe('jwt-token')
    expect(s.user.id).toBe(7)
    expect(s.user.username).toBe('alice')
    expect(s.user.name).toBe('alice') // name 取 username
    expect(s.user.role).toBe('admin')
    expect(typeof s.createdAt).toBe('string')
  })
})

describe('updateSessionUser', () => {
  it('refreshes user but keeps token', () => {
    const s = toAuthSession(API_PAYLOAD)
    const updated = updateSessionUser(s, { ...API_PAYLOAD.user, role: 'user' })
    expect(updated.token).toBe('jwt-token')
    expect(updated.user.role).toBe('user')
  })
})

describe('readStoredSession / persistSession / clearStoredSession', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('round-trips a valid session', () => {
    const s = toAuthSession(API_PAYLOAD)
    persistSession(s)
    const read = readStoredSession()
    expect(read?.user.email).toBe('alice@example.com')
    expect(read?.token).toBe('jwt-token')
  })

  it('returns null when nothing stored', () => {
    expect(readStoredSession()).toBeNull()
  })

  it('returns null for malformed JSON', () => {
    window.localStorage.setItem(AUTH_STORAGE_KEY, '{not json')
    expect(readStoredSession()).toBeNull()
  })

  it('rejects session missing token', () => {
    const bad = { user: API_PAYLOAD.user } as unknown as AuthSession
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(bad))
    expect(readStoredSession()).toBeNull()
  })

  it('rejects invalid role', () => {
    const bad = { ...toAuthSession(API_PAYLOAD) }
    bad.user = { ...bad.user, role: 'superadmin' as never }
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(bad))
    expect(readStoredSession()).toBeNull()
  })

  it('rejects non-numeric user id', () => {
    const bad = { ...toAuthSession(API_PAYLOAD) }
    bad.user = { ...bad.user, id: 'x' as never }
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(bad))
    expect(readStoredSession()).toBeNull()
  })

  it('clearStoredSession removes the entry', () => {
    persistSession(toAuthSession(API_PAYLOAD))
    clearStoredSession()
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
  })
})
