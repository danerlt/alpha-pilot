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

interface RuntimeConfig {
  trading_mode: 'testnet' | 'mainnet'
  llm_provider: string
  llm_model: string
  max_position_size_pct: number
  max_daily_loss_pct: number
  max_consecutive_losses: number
  max_single_risk_pct: number
  binance_testnet_configured: boolean
  binance_mainnet_configured: boolean
  llm_api_key_configured: boolean
  config_source: string
}

interface RuntimeConfigForm {
  trading_mode: 'testnet' | 'mainnet'
  binance_testnet_api_key: string
  binance_testnet_api_secret: string
  binance_mainnet_api_key: string
  binance_mainnet_api_secret: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api'

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    cache: 'no-store',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
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

function getEnvLabel(basePath: string) {
  if (!basePath || basePath === 'local') return 'local'
  if (basePath === '/ap-dev') return 'dev'
  if (basePath === '/ap-test') return 'test'
  if (basePath === '/ap') return 'prod'
  return basePath.replace(/^\//, '')
}

function isProductionEnv(basePath: string, tradingMode?: string) {
  return basePath === '/ap' || tradingMode === 'mainnet'
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
  const [runtimeConfig, setRuntimeConfig] = useState<RuntimeConfig | null>(null)
  const [configForm, setConfigForm] = useState<RuntimeConfigForm>({
    trading_mode: 'testnet',
    binance_testnet_api_key: '',
    binance_testnet_api_secret: '',
    binance_mainnet_api_key: '',
    binance_mainnet_api_secret: '',
  })
  const [savingConfig, setSavingConfig] = useState(false)
  const [configMessage, setConfigMessage] = useState<string | null>(null)
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
      const [h, a, p, t, d, r, c] = await Promise.all([
        fetchJson<HealthData>('/health'),
        fetchJson<AccountData>('/account').catch(() => null),
        fetchJson<Position[]>('/positions').catch(() => []),
        fetchJson<Trade[]>('/trades?limit=20').catch(() => []),
        fetchJson<Decision[]>('/decisions?limit=20').catch(() => []),
        fetchJson<RiskEvent[]>('/risk-events?limit=20').catch(() => []),
        fetchJson<RuntimeConfig>('/config/runtime').catch(() => null),
      ])
      setHealth(h)
      setAccount(a)
      setPositions(p)
      setTrades(t)
      setDecisions(d)
      setRiskEvents(r)
      setRuntimeConfig(c)
      if (c) {
        setConfigForm((prev) => ({
          ...prev,
          trading_mode: c.trading_mode,
        }))
      }
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
    const wsBase = `${proto}//${window.location.host}`
    // 从 API base 推导 WS 路径：/ap-dev/api → /ap-dev/ws，/api → /ws
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || '/api'
    const wsPath = apiBase.replace(/\/api$/, '/ws')
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

  const envBasePath = process.env.NEXT_PUBLIC_BASE_PATH || 'local'
  const env = getEnvLabel(envBasePath)
  const prodLike = isProductionEnv(envBasePath, health?.trading_mode)

  const handleClosePosition = async (id: number, symbol: string) => {
    const confirmed = confirm(
      prodLike
        ? `⚠️ 当前为高风险环境（${health?.trading_mode?.toUpperCase() || env.toUpperCase()}）。确认手动平仓 ${symbol}？`
        : `确认手动平仓 ${symbol}？`
    )
    if (!confirmed) return

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
    const firstConfirm = confirm(
      prodLike
        ? '⚠️ 当前为高风险环境。确认一键平仓所有持仓？此操作不可撤销。'
        : '确认一键平仓所有持仓？此操作不可撤销。'
    )
    if (!firstConfirm) return

    if (prodLike) {
      const typed = window.prompt('请输入 CLOSE ALL 确认执行一键平仓')
      if (typed !== 'CLOSE ALL') {
        alert('已取消：确认口令不匹配')
        return
      }
    }

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

  const handleResolveRisk = async (id: number, description: string) => {
    const confirmed = confirm(
      prodLike
        ? `⚠️ 当前为高风险环境。确认解除该风控事件？\n${description}`
        : `确认解除该风控事件？\n${description}`
    )
    if (!confirmed) return

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

  const handleConfigChange = (field: keyof RuntimeConfigForm, value: string) => {
    setConfigForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSaveRuntimeConfig = async () => {
    setSavingConfig(true)
    setConfigMessage(null)
    try {
      const payload: Record<string, string> = {
        trading_mode: configForm.trading_mode,
      }
      if (configForm.binance_testnet_api_key.trim()) payload.binance_testnet_api_key = configForm.binance_testnet_api_key.trim()
      if (configForm.binance_testnet_api_secret.trim()) payload.binance_testnet_api_secret = configForm.binance_testnet_api_secret.trim()
      if (configForm.binance_mainnet_api_key.trim()) payload.binance_mainnet_api_key = configForm.binance_mainnet_api_key.trim()
      if (configForm.binance_mainnet_api_secret.trim()) payload.binance_mainnet_api_secret = configForm.binance_mainnet_api_secret.trim()

      const updated = await postJson<RuntimeConfig>('/config/runtime', payload)
      setRuntimeConfig(updated)
      setConfigForm((prev) => ({
        ...prev,
        trading_mode: updated.trading_mode,
        binance_testnet_api_key: '',
        binance_testnet_api_secret: '',
        binance_mainnet_api_key: '',
        binance_mainnet_api_secret: '',
      }))
      setConfigMessage('运行时配置已保存，并已热更新到当前进程')
      await loadData()
    } catch (e) {
      setConfigMessage(`保存失败: ${e instanceof Error ? e.message : e}`)
    } finally {
      setSavingConfig(false)
    }
  }

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
        {prodLike && (
          <section className={styles.alertBanner}>
            <strong>高风险环境</strong>
            <span>
              当前控制台连接到 {health?.trading_mode?.toUpperCase() || env.toUpperCase()} 环境。
              手动平仓、解除熔断、一键操作都应视为危险动作。
            </span>
          </section>
        )}

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>运行时配置中心</h2>
            {runtimeConfig && <span className={styles.badge}>{runtimeConfig.config_source}</span>}
          </div>

          <div className={styles.configGrid}>
            <div className={styles.configBlock}>
              <label className={styles.fieldLabel}>当前模式</label>
              <select
                className={styles.input}
                value={configForm.trading_mode}
                onChange={(e) => handleConfigChange('trading_mode', e.target.value)}
              >
                <option value="testnet">TESTNET</option>
                <option value="mainnet">MAINNET</option>
              </select>
              <p className={styles.fieldHint}>切换后新的运行时配置会立即生效。</p>
            </div>

            <div className={styles.configBlock}>
              <label className={styles.fieldLabel}>Testnet API Key</label>
              <input
                className={styles.input}
                type="password"
                placeholder={runtimeConfig?.binance_testnet_configured ? '已配置，留空则不改' : '输入新的 Testnet API Key'}
                value={configForm.binance_testnet_api_key}
                onChange={(e) => handleConfigChange('binance_testnet_api_key', e.target.value)}
              />
              <label className={styles.fieldLabel}>Testnet API Secret</label>
              <input
                className={styles.input}
                type="password"
                placeholder={runtimeConfig?.binance_testnet_configured ? '已配置，留空则不改' : '输入新的 Testnet API Secret'}
                value={configForm.binance_testnet_api_secret}
                onChange={(e) => handleConfigChange('binance_testnet_api_secret', e.target.value)}
              />
            </div>

            <div className={styles.configBlock}>
              <label className={styles.fieldLabel}>Mainnet API Key</label>
              <input
                className={styles.input}
                type="password"
                placeholder={runtimeConfig?.binance_mainnet_configured ? '已配置，留空则不改' : '输入新的 Mainnet API Key'}
                value={configForm.binance_mainnet_api_key}
                onChange={(e) => handleConfigChange('binance_mainnet_api_key', e.target.value)}
              />
              <label className={styles.fieldLabel}>Mainnet API Secret</label>
              <input
                className={styles.input}
                type="password"
                placeholder={runtimeConfig?.binance_mainnet_configured ? '已配置，留空则不改' : '输入新的 Mainnet API Secret'}
                value={configForm.binance_mainnet_api_secret}
                onChange={(e) => handleConfigChange('binance_mainnet_api_secret', e.target.value)}
              />
            </div>
          </div>

          <div className={styles.configStatusRow}>
            <span className={styles.statusPill} data-on={runtimeConfig?.binance_testnet_configured ? 'true' : 'false'}>
              Testnet 凭据 {runtimeConfig?.binance_testnet_configured ? '已配置' : '未配置'}
            </span>
            <span className={styles.statusPill} data-on={runtimeConfig?.binance_mainnet_configured ? 'true' : 'false'}>
              Mainnet 凭据 {runtimeConfig?.binance_mainnet_configured ? '已配置' : '未配置'}
            </span>
          </div>

          <div className={styles.configActionRow}>
            <button className={styles.primaryBtn} onClick={handleSaveRuntimeConfig} disabled={savingConfig}>
              {savingConfig ? '保存中…' : '保存并热更新'}
            </button>
            {configMessage && <span className={styles.fieldHint}>{configMessage}</span>}
          </div>
        </section>

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
                          onClick={() => handleClosePosition(p.id, p.symbol)}
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
                            onClick={() => handleResolveRisk(r.id, r.description)}
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
