import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, buildAuthHeaders, ERROR_CODES, type ApiError } from './api'

function mockFetchOnce(body: unknown, init: { ok?: boolean; status?: number } = {}) {
  const ok = init.ok ?? true
  const status = init.status ?? 200
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok,
    status,
    json: async () => body,
  })))
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('buildAuthHeaders', () => {
  it('adds bearer token', () => {
    expect(buildAuthHeaders('tok')).toEqual({ Authorization: 'Bearer tok' })
  })

  it('adds content-type when hasBody', () => {
    expect(buildAuthHeaders('tok', true)).toEqual({
      'Content-Type': 'application/json',
      Authorization: 'Bearer tok',
    })
  })

  it('omits authorization when no token', () => {
    expect(buildAuthHeaders(undefined, true)).toEqual({ 'Content-Type': 'application/json' })
  })
})

describe('apiRequest envelope parsing', () => {
  it('unwraps data on success envelope', async () => {
    mockFetchOnce({ success: true, code: '0', message: '成功', data: { foo: 42 } })
    const result = await apiRequest<{ foo: number }>('/x')
    expect(result).toEqual({ foo: 42 })
  })

  it('throws ApiError with code on business-error envelope', async () => {
    mockFetchOnce({ success: false, code: ERROR_CODES.RISK_REJECTED, message: '风控拒绝', request_id: 'r1' })
    await expect(apiRequest('/x', { skipAuthRedirect: true })).rejects.toMatchObject({
      code: ERROR_CODES.RISK_REJECTED,
      requestId: 'r1',
    })
  })

  it('throws with HTTP status on transport error', async () => {
    mockFetchOnce({}, { ok: false, status: 500 })
    await expect(apiRequest('/x')).rejects.toMatchObject({ status: 500 })
  })

  it('returns null data as undefined-safe', async () => {
    mockFetchOnce({ success: true, code: '0', message: '成功', data: null })
    const result = await apiRequest('/x')
    expect(result).toBeUndefined()
  })

  it('AUTH_ERROR triggers logout redirect unless skipped', async () => {
    // 不 skip → 触发 handleUnauthorized 写 window.location.href
    window.localStorage.setItem('alpha-pilot-session', '{}')
    const hrefSetter = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { pathname: '/', set href(v: string) { hrefSetter(v) } },
      writable: true,
    })
    mockFetchOnce({ success: false, code: ERROR_CODES.AUTH_ERROR, message: '未授权' })
    await expect(apiRequest('/x')).rejects.toMatchObject({ code: ERROR_CODES.AUTH_ERROR })
    expect(hrefSetter).toHaveBeenCalledWith('/login?reason=session_expired')
  })

  it('skipAuthRedirect avoids redirect on AUTH_ERROR', async () => {
    const hrefSetter = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { pathname: '/', set href(v: string) { hrefSetter(v) } },
      writable: true,
    })
    mockFetchOnce({ success: false, code: ERROR_CODES.AUTH_ERROR, message: '未授权' })
    await expect(apiRequest('/x', { skipAuthRedirect: true })).rejects.toBeTruthy()
    expect(hrefSetter).not.toHaveBeenCalled()
  })
})

describe('ApiError shape', () => {
  it('carries code and requestId fields', async () => {
    mockFetchOnce({ success: false, code: '400001', message: 'bad', request_id: 'req-9' })
    try {
      await apiRequest('/x', { skipAuthRedirect: true })
      throw new Error('should have thrown')
    } catch (e) {
      const err = e as ApiError
      expect(err.code).toBe('400001')
      expect(err.requestId).toBe('req-9')
    }
  })
})
