'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { RouteGuard } from '@/components/route-guard'
import { useAuth } from '@/components/auth-provider'
import { apiRequest, buildAuthHeaders } from '@/lib/api'
import { UserRole, UserStatus } from '@/lib/auth'

interface AdminUser {
  id: number
  username: string
  email: string
  role: UserRole
  status: UserStatus
  last_login_at: string | null
  created_at: string | null
  updated_at: string | null
}

function fmtTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

export default function AdminUsersPage() {
  const { session } = useAuth()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [savingId, setSavingId] = useState<number | null>(null)

  const token = session?.token

  const loadUsers = async () => {
    if (!token) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiRequest<AdminUser[]>('/admin/users', {
        headers: buildAuthHeaders(token),
      })
      setUsers(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [token])

  const filteredUsers = useMemo(() => {
    const keyword = query.trim().toLowerCase()
    return users.filter((user) => !keyword || [user.username, user.email, user.role, user.status].join(' ').toLowerCase().includes(keyword))
  }, [query, users])

  const patchUser = async (userId: number, payload: Partial<Pick<AdminUser, 'role' | 'status'>>) => {
    if (!token) return
    setSavingId(userId)
    setError(null)
    setMessage(null)
    try {
      const updated = await apiRequest<AdminUser>(`/admin/users/${userId}`, {
        method: 'PATCH',
        headers: buildAuthHeaders(token, true),
        body: JSON.stringify(payload),
      })
      setUsers((prev) => prev.map((item) => item.id === userId ? updated : item))
      setMessage(`已更新用户 #${userId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新用户失败')
    } finally {
      setSavingId(null)
    }
  }

  return (
    <RouteGuard requireRole="admin">
      <main className="adminPage">
        <section className="adminHero adminHeroCompact">
          <span className="authEyebrow">Admin / Users</span>
          <h1>用户管理</h1>
          <p>直接对接 admin users API。支持查看用户清单，并在页面内调整角色和状态。</p>
          <div className="adminHeroActions">
            <Link href="/admin" className="shellGhostButton">返回后台首页</Link>
          </div>
        </section>

        <section className="currencyToolbar">
          <div className="currencySearch">
            <label htmlFor="user-search">用户搜索</label>
            <input id="user-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="按用户名 / 邮箱 / 角色 / 状态搜索" />
          </div>
        </section>

        <section className="currencyTableCard">
          <div className="currencyTableHeader">
            <div>
              <h2>用户列表</h2>
              <p>{loading ? '正在加载真实 API 数据…' : '支持角色与状态即时更新。'}</p>
            </div>
            <span className="currencyCount">{filteredUsers.length} / {users.length} 个用户</span>
          </div>

          {(error || message) && (
            <div className={error ? 'authError' : 'authHint'} style={{ marginTop: 16 }}>
              {error || message}
            </div>
          )}

          <div className="currencyTableWrap adminDesktopOnly">
            <table className="currencyTable">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>最近登录</th>
                  <th>创建时间</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>
                      <strong>{user.username}</strong>
                      <div className="currencyMeta">{user.email}</div>
                    </td>
                    <td>
                      <select value={user.role} disabled={savingId === user.id} onChange={(e) => patchUser(user.id, { role: e.target.value as UserRole })}>
                        <option value="user">user</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td>
                      <select value={user.status} disabled={savingId === user.id} onChange={(e) => patchUser(user.id, { status: e.target.value as UserStatus })}>
                        <option value="active">active</option>
                        <option value="disabled">disabled</option>
                      </select>
                    </td>
                    <td>{fmtTime(user.last_login_at)}</td>
                    <td>{fmtTime(user.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="adminMobileList adminMobileOnly">
            {filteredUsers.map((user) => (
              <article key={user.id} className="adminMobileCard">
                <div className="adminMobileCardHeader">
                  <div>
                    <strong>{user.username}</strong>
                    <p>{user.email}</p>
                  </div>
                  <span className="currencyStatus" data-status={user.status === 'active' ? '启用' : '停用'}>{user.status}</span>
                </div>
                <div className="adminFormGrid">
                  <label className="authField">
                    <span>角色</span>
                    <select value={user.role} disabled={savingId === user.id} onChange={(e) => patchUser(user.id, { role: e.target.value as UserRole })}>
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                    </select>
                  </label>
                  <label className="authField">
                    <span>状态</span>
                    <select value={user.status} disabled={savingId === user.id} onChange={(e) => patchUser(user.id, { status: e.target.value as UserStatus })}>
                      <option value="active">active</option>
                      <option value="disabled">disabled</option>
                    </select>
                  </label>
                </div>
                <div className="adminMobileMeta">
                  <span>ID：{user.id}</span>
                  <span>最近登录：{fmtTime(user.last_login_at)}</span>
                  <span>创建时间：{fmtTime(user.created_at)}</span>
                </div>
              </article>
            ))}
          </div>

          {!loading && filteredUsers.length === 0 && <div className="authHint">当前没有匹配的用户。</div>}
        </section>
      </main>
    </RouteGuard>
  )
}
