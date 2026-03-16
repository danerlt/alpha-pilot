'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import styles from './page.module.css'

// ─── Types ────────────────────────────────────────────────────────────────────

interface HealthData {
  status: string
  trading_mode: string
  version: string
}

interface AccountData {
  total_balance_usdt?: number
  available_balance_usdt?: number
  unrealized_pnl?: number
  daily_pnl?: number
  daily_pnl_pct?: number
  snapshot_at?: string
  message?: string
}

interface Position {
  id: number
  symbol: string
  quantity: number
  entry_price: number
  current_price: number
  stop_loss: number
  take_profit: number | null
  unrealized_pnl: number
  unrealized_pnl_pct: number
  opened_at: string
}

interface Trade {
  id: number
  symbol: string
  quantity: number
  entry_price: number
  exit_price: number
  pnl: number
  pnl_pct: number
  exit_reason: string
  regime: string
  opened_at: string
  closed_at: string
  holding_seconds: number
}

interface Decision {
  id: number
  symbol: string
  timeframe: string
  action: string
  confidence: number | null
  strategy_mode: string | null
  reasoning: string | null
  risk_note: string | null
  is_fallback: boolean
  decided_at: string
}

interface RiskEvent {
  id: number
  event_type: string
  symbol: string | null
  description: string
  resolved: boolean
  triggered_at: string
  resolved_at: string | null
}

interface LiveEvent {
  type: string
  symbol?: string
  action?: string
  result?: string
  reason?: string
  ts?: string
  [key: string]: unknown
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function postJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function fmtHolding(seconds: number) {
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  return `${Math.floor(seconds / 86400)}d`
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [account, setAccount] = useState<AccountData | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [trades, setTrades] = useState<Trade[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [riskEvents, setRiskEvents] = useState<RiskEvent[]>([])
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed'>('connecting')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [closingId, setClosingId] = useState<number | null>(null)
  const [closingAll, setClosingAll] = useState(false)
  const [resolvingId, setResolvingId] = useState<number | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [h, a, p, t, d, r] = await Promise.all([
        fetchJson<HealthData>('/health'),
        fetchJson<AccountData>('/account').catch(() => null),
        fetchJson<Position[]>('/positions').catch(() => []),
        fetchJson<Trade[]>('/trades?limit=20').catch(() => []),
        fetchJson<Decision[]>('/decisions?limit=20').catch(() => []),
        fetchJson<RiskEvent[]>('/risk-events?limit=20').catch(() => []),
      ])
      setHealth(h)
      setAccount(a)
      setPositions(p)
      setTrades(t)
      setDecisions(d)
      setRiskEvents(r)
      setLastRefresh(new Date())
    } catch (e) {
      setError(e instanceof Error ? e.message : '连接后端失败')
    } finally {
      setLoading(false)
    }
  }, [])

  // WebSocket setup
  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsBase = process.env.NEXT_PUBLIC_WS_BASE || `${proto}//${window.location.host}`
    const wsPath = process.env.NEXT_PUBLIC_WS_PATH || '/ws'
    const url = `${wsBase}${wsPath}`

    let ws: WebSocket
    let reconnectTimer: ReturnType<typeof setTimeout>

    const connect = () => {
      ws = new WebSocket(url)
      wsRef.current = ws
      setWsStatus('connecting')

      ws.onopen = () => setWsStatus('open')
      ws.onclose = () => {
        setWsStatus('closed')
        reconnectTimer = setTimeout(connect, 5000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data) as LiveEvent
          setLiveEvents((prev) => [data, ...prev].slice(0, 50))
          // 重要事件触发数据刷新
          if (data.type && ['order_executed', 'position_closed', 'circuit_breaker'].includes(data.type)) {
            loadData()
          }
        } catch {
          // ignore malformed messages
        }
      }
    }

    connect()
    return () => {
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [loadData])

  useEffect(() => {
    loadData()
    const t = setInterval(loadData, 30000)
    return () => clearInterval(t)
  }, [loadData])

  const handleClosePosition = async (id: number) => {
    setClosingId(id)
    try {
      await postJson(`/positions/${id}/close`)
      await loadData()
    } catch (e) {
      alert(`平仓失败: ${e instanceof Error ? e.message : e}`)
    } finally {
      setClosingId(null)
    }
  }

  const handleCloseAll = async () => {
    if (!confirm('确认一键平仓所有持仓？此操作不可撤销。')) return
    setClosingAll(true)
    try {
      const result = await postJson<{ count: number }>('/positions/close-all')
      alert(`已平仓 ${result.count} 个持仓`)
      await loadData()
    } catch (e) {
      alert(`平仓失败: ${e instanceof Error ? e.message : e}`)
    } finally {
      setClosingAll(false)
    }
  }

  const handleResolveRisk = async (id: number) => {
    setResolvingId(id)
    try {
      await postJson(`/risk-events/${id}/resolve`)
      await loadData()
    } catch (e) {
      alert(`解除失败: ${e instanceof Error ? e.message : e}`)
    } finally {
      setResolvingId(null)
    }
  }

  const env = process.env.NEXT_PUBLIC_BASE_PATH || 'local'
  const unresolvedRisk = riskEvents.filter((r) => !r.resolved).length

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⚡</span>
          <span>AlphaPilot</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.wsDot} data-status={wsStatus} title={`WebSocket: ${wsStatus}`} />
          <span className={styles.envBadge} data-env={env || 'local'}>
            {env || 'local'}
          </span>
          <button className={styles.refreshBtn} onClick={loadData} disabled={loading}>
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
      </header>

      <div className={styles.content}>
        {/* 系统状态 */}
        <div className={styles.row2}>
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>系统状态</h2>
            {error ? (
              <div className={styles.statusRow}>
                <span className={styles.dot} data-status="error" />
                <span className={styles.statusLabel}>后端离线</span>
                <span className={styles.statusDetail}>{error}</span>
              </div>
            ) : health ? (
              <div className={styles.statusGrid}>
                <div className={styles.statusRow}>
                  <span className={styles.dot} data-status="ok" />
                  <span className={styles.statusLabel}>后端</span>
                  <span className={styles.statusDetail}>在线 v{health.version}</span>
                </div>
                <div className={styles.statusRow}>
                  <span className={styles.dot} data-status={health.trading_mode === 'mainnet' ? 'warn' : 'ok'} />
                  <span className={styles.statusLabel}>交易模式</span>
                  <span className={styles.statusDetail}>{health.trading_mode.toUpperCase()}</span>
                </div>
                <div className={styles.statusRow}>
                  <span className={styles.dot} data-status={wsStatus === 'open' ? 'ok' : wsStatus === 'connecting' ? 'warn' : 'error'} />
                  <span className={styles.statusLabel}>实时推送</span>
                  <span className={styles.statusDetail}>
                    {wsStatus === 'open' ? '已连接' : wsStatus === 'connecting' ? '连接中…' : '已断开'}
                  </span>
                </div>
              </div>
            ) : (
              <div className={styles.skeleton} />
            )}
          </section>

          {/* 账户概览 */}
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>账户概览</h2>
            {account && !account.message ? (
              <div className={styles.statsGrid}>
                <div className={styles.stat}>
                  <div className={styles.statLabel}>总余额</div>
                  <div className={styles.statValue}>
                    {account.total_balance_usdt?.toFixed(2) ?? '—'} <small>USDT</small>
                  </div>
                </div>
                <div className={styles.stat}>
                  <div className={styles.statLabel}>可用余额</div>
                  <div className={styles.statValue}>
                    {account.available_balance_usdt?.toFixed(2) ?? '—'} <small>USDT</small>
                  </div>
                </div>
                <div className={styles.stat}>
                  <div className={styles.statLabel}>今日盈亏</div>
                  <div
                    className={styles.statValue}
                    data-sign={(account.daily_pnl ?? 0) >= 0 ? 'pos' : 'neg'}
                  >
                    {(account.daily_pnl ?? 0) >= 0 ? '+' : ''}
                    {account.daily_pnl?.toFixed(2) ?? '—'} USDT
                    <small> ({((account.daily_pnl_pct ?? 0) * 100).toFixed(2)}%)</small>
                  </div>
                </div>
              </div>
            ) : (
              <p className={styles.empty}>暂无账户快照（运行策略循环后自动同步）</p>
            )}
          </section>
        </div>

        {/* 当前持仓 */}
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>
              当前持仓 <span className={styles.badge}>{positions.length}</span>
            </h2>
            {positions.length > 0 && (
              <button className={styles.dangerBtn} onClick={handleCloseAll} disabled={closingAll}>
                {closingAll ? '平仓中…' : '一键平仓'}
              </button>
            )}
          </div>
          {positions.length === 0 ? (
            <p className={styles.empty}>暂无开仓持仓</p>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>币种</th><th>数量</th><th>开仓价</th><th>现价</th>
                    <th>止损</th><th>止盈</th><th>未实现盈亏</th><th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((p) => (
                    <tr key={p.id}>
                      <td><strong>{p.symbol}</strong></td>
                      <td>{p.quantity.toFixed(6)}</td>
                      <td>{p.entry_price.toFixed(2)}</td>
                      <td>{p.current_price.toFixed(2)}</td>
                      <td>{p.stop_loss.toFixed(2)}</td>
                      <td>{p.take_profit?.toFixed(2) ?? '—'}</td>
                      <td data-sign={p.unrealized_pnl >= 0 ? 'pos' : 'neg'}>
                        {p.unrealized_pnl >= 0 ? '+' : ''}
                        {p.unrealized_pnl.toFixed(4)}
                        <small> ({(p.unrealized_pnl_pct * 100).toFixed(2)}%)</small>
                      </td>
                      <td>
                        <button
                          className={styles.smallDangerBtn}
                          onClick={() => handleClosePosition(p.id)}
                          disabled={closingId === p.id}
                        >
                          {closingId === p.id ? '…' : '平仓'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 风控事件 */}
        {(riskEvents.length > 0 || unresolvedRisk > 0) && (
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>
              风控事件
              {unresolvedRisk > 0 && <span className={styles.badgeWarn}>{unresolvedRisk} 未解除</span>}
            </h2>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>类型</th><th>描述</th><th>触发时间</th><th>状态</th><th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {riskEvents.map((r) => (
                    <tr key={r.id}>
                      <td><code className={styles.code}>{r.event_type}</code></td>
                      <td>{r.description}</td>
                      <td>{fmtTime(r.triggered_at)}</td>
                      <td>
                        <span className={styles.statusTag} data-resolved={r.resolved}>
                          {r.resolved ? '已解除' : '活跃'}
                        </span>
                      </td>
                      <td>
                        {!r.resolved && (
                          <button
                            className={styles.smallBtn}
                            onClick={() => handleResolveRisk(r.id)}
                            disabled={resolvingId === r.id}
                          >
                            {resolvingId === r.id ? '…' : '解除熔断'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* AI 决策日志 + 实时事件 */}
        <div className={styles.row2}>
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>AI 决策日志</h2>
            {decisions.length === 0 ? (
              <p className={styles.empty}>暂无决策记录</p>
            ) : (
              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr><th>时间</th><th>币种</th><th>动作</th><th>置信度</th><th>是否兜底</th></tr>
                  </thead>
                  <tbody>
                    {decisions.map((d) => (
                      <tr key={d.id}>
                        <td>{fmtTime(d.decided_at)}</td>
                        <td>{d.symbol}</td>
                        <td>
                          <span className={styles.actionTag} data-action={d.action}>
                            {d.action}
                          </span>
                        </td>
                        <td>{d.confidence != null ? `${(d.confidence * 100).toFixed(0)}%` : '—'}</td>
                        <td>{d.is_fallback ? <span className={styles.fallbackTag}>兜底</span> : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* 实时事件流 */}
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>
              实时事件流
              <span className={styles.wsDotInline} data-status={wsStatus} />
            </h2>
            {liveEvents.length === 0 ? (
              <p className={styles.empty}>等待事件推送…</p>
            ) : (
              <div className={styles.eventList}>
                {liveEvents.slice(0, 15).map((e, i) => (
                  <div key={i} className={styles.eventItem}>
                    <span className={styles.eventType} data-type={e.type}>{e.type}</span>
                    {e.symbol && <span className={styles.eventSymbol}>{e.symbol}</span>}
                    {e.action && <span className={styles.eventDetail}>{e.action}</span>}
                    {e.reason && <span className={styles.eventReason}>{e.reason}</span>}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* 交易记录 */}
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>交易记录 <span className={styles.badge}>{trades.length}</span></h2>
          {trades.length === 0 ? (
            <p className={styles.empty}>暂无已平仓交易</p>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>时间</th><th>币种</th><th>开仓价</th><th>平仓价</th>
                    <th>盈亏</th><th>持仓时长</th><th>平仓原因</th><th>市场状态</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t) => (
                    <tr key={t.id}>
                      <td>{fmtTime(t.closed_at)}</td>
                      <td>{t.symbol}</td>
                      <td>{t.entry_price.toFixed(2)}</td>
                      <td>{t.exit_price.toFixed(2)}</td>
                      <td data-sign={t.pnl >= 0 ? 'pos' : 'neg'}>
                        {t.pnl >= 0 ? '+' : ''}{t.pnl.toFixed(4)}
                        <small> ({(t.pnl_pct * 100).toFixed(2)}%)</small>
                      </td>
                      <td>{fmtHolding(t.holding_seconds)}</td>
                      <td><code className={styles.code}>{t.exit_reason}</code></td>
                      <td>{t.regime ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Footer */}
        <p className={styles.footer}>
          {lastRefresh && `最后刷新：${lastRefresh.toLocaleTimeString('zh-CN')} · 每 30 秒自动刷新`}
        </p>
      </div>
    </main>
  )
}
