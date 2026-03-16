'use client'

import { useEffect, useState } from 'react'
import styles from './page.module.css'

interface HealthData {
  status: string
  trading_mode: string
  version: string
}

interface AccountData {
  total_balance_usdt?: number
  available_balance_usdt?: number
  daily_pnl?: number
  daily_pnl_pct?: number
  snapshot_at?: string
  message?: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [account, setAccount] = useState<AccountData | null>(null)
  const [positions, setPositions] = useState<unknown[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [h, a, p] = await Promise.all([
        fetchJson<HealthData>('/health'),
        fetchJson<AccountData>('/account').catch(() => null),
        fetchJson<unknown[]>('/positions').catch(() => []),
      ])
      setHealth(h)
      setAccount(a)
      setPositions(p)
      setLastRefresh(new Date())
    } catch (e) {
      setError(e instanceof Error ? e.message : '连接后端失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const t = setInterval(loadData, 15000)
    return () => clearInterval(t)
  }, [])

  const env = process.env.NEXT_PUBLIC_BASE_PATH || 'local'

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⚡</span>
          <span>AlphaPilot</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.envBadge} data-env={env || 'local'}>
            {env || 'local'}
          </span>
          <button className={styles.refreshBtn} onClick={loadData} disabled={loading}>
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
      </header>

      <div className={styles.content}>
        {/* 连接状态 */}
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
                  <small>
                    {' '}({((account.daily_pnl_pct ?? 0) * 100).toFixed(2)}%)
                  </small>
                </div>
              </div>
            </div>
          ) : (
            <p className={styles.empty}>暂无账户快照（运行策略循环后自动同步）</p>
          )}
        </section>

        {/* 当前持仓 */}
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>当前持仓 <span className={styles.badge}>{positions.length}</span></h2>
          {positions.length === 0 ? (
            <p className={styles.empty}>暂无开仓持仓</p>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>币种</th><th>数量</th><th>开仓价</th><th>现价</th><th>止损</th><th>未实现盈亏</th>
                  </tr>
                </thead>
                <tbody>
                  {(positions as Record<string, unknown>[]).map((p, i) => (
                    <tr key={i}>
                      <td>{String(p.symbol)}</td>
                      <td>{Number(p.quantity).toFixed(6)}</td>
                      <td>{Number(p.entry_price).toFixed(2)}</td>
                      <td>{Number(p.current_price).toFixed(2)}</td>
                      <td>{Number(p.stop_loss).toFixed(2)}</td>
                      <td data-sign={Number(p.unrealized_pnl) >= 0 ? 'pos' : 'neg'}>
                        {Number(p.unrealized_pnl) >= 0 ? '+' : ''}
                        {Number(p.unrealized_pnl).toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 刷新时间 */}
        <p className={styles.footer}>
          最后刷新：{lastRefresh.toLocaleTimeString('zh-CN')} · 每 15 秒自动刷新
        </p>
      </div>
    </main>
  )
}
