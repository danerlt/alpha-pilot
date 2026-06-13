'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { RouteGuard } from '@/components/route-guard'
import { useAuth } from '@/components/auth-provider'
import { apiRequest, buildAuthHeaders } from '@/lib/api'

interface AuditLogItem {
  id: number
  user_id: number | null
  actor: string | null
  action: string
  resource_type: string
  resource_id: string | null
  before_json: Record<string, unknown> | null
  after_json: Record<string, unknown> | null
  ip: string | null
  user_agent: string | null
  created_at: string | null
}

function actorLabel(item: AuditLogItem) {
  if (item.actor) return item.actor
  if (item.user_id != null) return `#${item.user_id}`
  return '—'
}

function fmtTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function summarizeChange(item: AuditLogItem) {
  const beforeKeys = item.before_json ? Object.keys(item.before_json) : []
  const afterKeys = item.after_json ? Object.keys(item.after_json) : []
  const keys = Array.from(new Set([...beforeKeys, ...afterKeys]))
  if (keys.length === 0) return '无字段快照'
  return keys.slice(0, 3).join(' · ')
}

export default function AdminAuditLogsPage() {
  const { session } = useAuth()
  const token = session?.token
  const [items, setItems] = useState<AuditLogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [resourceFilter, setResourceFilter] = useState<'all' | 'symbol_config' | 'user'>('all')

  useEffect(() => {
    const loadAuditLogs = async () => {
      if (!token) return
      setLoading(true)
      setError(null)
      try {
        const data = await apiRequest<AuditLogItem[]>('/admin/audit-logs?limit=100', {
          headers: buildAuthHeaders(token),
        })
        setItems(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载审计日志失败')
      } finally {
        setLoading(false)
      }
    }

    void loadAuditLogs()
  }, [token])

  const filteredItems = useMemo(() => {
    const keyword = query.trim().toLowerCase()
    return items.filter((item) => {
      const matchesKeyword = !keyword || [item.action, item.resource_type, item.resource_id || '', item.actor || '', item.user_id || '', summarizeChange(item)]
        .join(' ')
        .toLowerCase()
        .includes(keyword)
      const matchesResource = resourceFilter === 'all' || item.resource_type === resourceFilter
      return matchesKeyword && matchesResource
    })
  }, [items, query, resourceFilter])

  return (
    <RouteGuard requireRole="admin">
      <main className="adminPage">
        <section className="adminHero adminHeroCompact adminSurfaceGlow">
          <div className="adminHeroSplit">
            <div className="adminHeroContent">
              <span className="authEyebrow">Admin / Audit Logs</span>
              <h1>审计日志</h1>
              <p>先补齐后台日志页骨架和列表结构：可筛选、可浏览、桌面表格 + 移动卡片，并为后续详情扩展留位置。</p>
              <div className="adminHeroActions">
                <Link href="/admin" className="shellGhostButton">返回后台首页</Link>
                <Link href="/admin/users" className="shellGhostButton">回到用户管理</Link>
              </div>
            </div>
            <div className="adminHighlightCard">
              <span className="adminHighlightLabel">日志总览</span>
              <strong>{loading ? '正在同步…' : `${filteredItems.length} / ${items.length} 条记录`}</strong>
              <p>当前覆盖 symbol_config 与 user 两类后台写操作，后续可继续补操作人映射与详情抽屉。</p>
            </div>
          </div>
        </section>

        <section className="currencyToolbar adminToolbarCard">
          <div className="currencySearch">
            <label htmlFor="audit-search">日志搜索</label>
            <input
              id="audit-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="按 action / resource / resource_id / 字段摘要搜索"
            />
          </div>
          <div className="currencyToolbarActions">
            <select value={resourceFilter} onChange={(e) => setResourceFilter(e.target.value as 'all' | 'symbol_config' | 'user')}>
              <option value="all">全部资源</option>
              <option value="symbol_config">symbol_config</option>
              <option value="user">user</option>
            </select>
          </div>
        </section>

        <section className="currencyTableCard adminDataCard">
          <div className="currencyTableHeader">
            <div>
              <h2>审计记录</h2>
              <p>{loading ? '正在加载真实 API 数据…' : '已连接真实 admin audit logs API。'}</p>
            </div>
            <span className="currencyCount">{filteredItems.length} / {items.length} 条</span>
          </div>

          {error && <div className="authError" style={{ marginTop: 16 }}>{error}</div>}

          <div className="currencyTableWrap adminDesktopOnly">
            <table className="currencyTable">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>动作</th>
                  <th>资源</th>
                  <th>操作人</th>
                  <th>字段摘要</th>
                  <th>来源</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id}>
                    <td>{fmtTime(item.created_at)}</td>
                    <td><span className="adminActionBadge">{item.action}</span></td>
                    <td>
                      <strong>{item.resource_type}</strong>
                      <div className="currencyMeta">ID: {item.resource_id || '—'}</div>
                    </td>
                    <td>{actorLabel(item)}</td>
                    <td>{summarizeChange(item)}</td>
                    <td>{item.ip || 'system'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="adminMobileList adminMobileOnly">
            {filteredItems.map((item) => (
              <article key={item.id} className="adminMobileCard adminRecordCard">
                <div className="adminMobileCardHeader">
                  <div>
                    <strong>{item.resource_type}</strong>
                    <p>{fmtTime(item.created_at)}</p>
                  </div>
                  <span className="adminActionBadge">{item.action}</span>
                </div>
                <div className="adminMobileMeta">
                  <span>资源 ID：{item.resource_id || '—'}</span>
                  <span>操作人：{actorLabel(item)}</span>
                  <span>字段摘要：{summarizeChange(item)}</span>
                  <span>来源：{item.ip || 'system'}</span>
                </div>
              </article>
            ))}
          </div>

          {!loading && filteredItems.length === 0 && <div className="authHint">当前筛选条件下没有审计记录。</div>}
        </section>
      </main>
    </RouteGuard>
  )
}
