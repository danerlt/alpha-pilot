'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { RouteGuard } from '@/components/route-guard'
import { useAuth } from '@/components/auth-provider'
import { apiRequest, buildAuthHeaders } from '@/lib/api'

interface SymbolConfig {
  id: number
  symbol: string
  base_asset: string
  quote_asset: string
  enabled: boolean
  timeframe: string
  max_position_size_pct: number | null
  priority: number
  sort_order: number
  notes: string | null
}

interface SymbolFormState {
  symbol: string
  base_asset: string
  quote_asset: string
  enabled: boolean
  timeframe: string
  max_position_size_pct: string
  priority: string
  sort_order: string
  notes: string
}

const EMPTY_FORM: SymbolFormState = {
  symbol: '',
  base_asset: '',
  quote_asset: 'USDT',
  enabled: true,
  timeframe: '15m',
  max_position_size_pct: '',
  priority: '100',
  sort_order: '100',
  notes: '',
}

function toFormState(item?: SymbolConfig): SymbolFormState {
  if (!item) return EMPTY_FORM
  return {
    symbol: item.symbol,
    base_asset: item.base_asset,
    quote_asset: item.quote_asset,
    enabled: item.enabled,
    timeframe: item.timeframe,
    max_position_size_pct: item.max_position_size_pct == null ? '' : String(item.max_position_size_pct),
    priority: String(item.priority),
    sort_order: String(item.sort_order),
    notes: item.notes || '',
  }
}

function formatStatus(enabled: boolean) {
  return enabled ? '启用' : '停用'
}

export default function AdminCurrenciesPage() {
  const { session } = useAuth()
  const [items, setItems] = useState<SymbolConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<SymbolFormState>(EMPTY_FORM)

  const token = session?.token

  const loadSymbols = async () => {
    if (!token) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiRequest<SymbolConfig[]>('/admin/symbols', {
        headers: buildAuthHeaders(token),
      })
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载符号配置失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadSymbols()
  }, [token])

  const filteredItems = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    return items.filter((item) => {
      const matchesKeyword = !keyword || [item.symbol, item.base_asset, item.quote_asset, item.notes || '']
        .join(' ')
        .toLowerCase()
        .includes(keyword)
      const matchesStatus = statusFilter === 'all'
        || (statusFilter === 'enabled' && item.enabled)
        || (statusFilter === 'disabled' && !item.enabled)
      return matchesKeyword && matchesStatus
    })
  }, [items, search, statusFilter])

  const startCreate = () => {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setMessage(null)
    setError(null)
  }

  const startEdit = (item: SymbolConfig) => {
    setEditingId(item.id)
    setForm(toFormState(item))
    setMessage(null)
    setError(null)
  }

  const submitForm = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) return

    if (!form.symbol.trim() || !form.base_asset.trim()) {
      setError('请至少填写 symbol 和 base asset')
      return
    }

    setSubmitting(true)
    setError(null)
    setMessage(null)

    const payload = {
      ...(editingId == null ? { symbol: form.symbol.trim().toUpperCase() } : {}),
      base_asset: form.base_asset.trim().toUpperCase(),
      quote_asset: form.quote_asset.trim().toUpperCase() || 'USDT',
      enabled: form.enabled,
      timeframe: form.timeframe.trim() || '15m',
      max_position_size_pct: form.max_position_size_pct.trim() ? Number(form.max_position_size_pct) : null,
      priority: Number(form.priority || 100),
      sort_order: Number(form.sort_order || 100),
      notes: form.notes.trim() || null,
    }

    try {
      if (editingId == null) {
        await apiRequest<SymbolConfig>('/admin/symbols', {
          method: 'POST',
          headers: buildAuthHeaders(token, true),
          body: JSON.stringify(payload),
        })
        setMessage('已新增符号配置')
      } else {
        await apiRequest<SymbolConfig>(`/admin/symbols/${editingId}`, {
          method: 'PATCH',
          headers: buildAuthHeaders(token, true),
          body: JSON.stringify(payload),
        })
        setMessage('已更新符号配置')
      }
      await loadSymbols()
      startCreate()
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交符号配置失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <RouteGuard requireRole="admin">
      <main className="adminPage">
        <section className="adminHero adminHeroCompact adminSurfaceGlow">
          <div className="adminHeroSplit">
            <div className="adminHeroContent">
              <span className="authEyebrow">Admin / Symbols</span>
              <h1>Symbol 管理</h1>
              <p>页面语义统一收口到 symbol management。桌面保留表格密度，移动端切成记录卡片，新增 / 编辑都在同一页完成。</p>
              <div className="adminHeroActions">
                <Link href="/admin" className="shellGhostButton">返回后台首页</Link>
                <button className="shellPrimaryButton" type="button" onClick={startCreate}>新建 Symbol</button>
              </div>
            </div>
            <div className="adminHighlightCard">
              <span className="adminHighlightLabel">当前范围</span>
              <strong>{loading ? '正在同步…' : `${filteredItems.length} / ${items.length} 个 Symbols`}</strong>
              <p>支持状态筛选、表单内编辑，以及更清晰的 symbol / base / quote 信息层级。</p>
            </div>
          </div>
        </section>

        <section className="currencyToolbar adminToolbarCard">
          <div className="currencySearch">
            <label htmlFor="symbol-search">Symbol 搜索</label>
            <input id="symbol-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="例如 BTC / ETH / SOL" />
          </div>
          <div className="currencyToolbarActions">
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as 'all' | 'enabled' | 'disabled')}>
              <option value="all">全部状态</option>
              <option value="enabled">仅启用</option>
              <option value="disabled">仅停用</option>
            </select>
          </div>
        </section>

        <section className="adminHeroStats adminStatsStrip">
          <div className="adminMetricTile">
            <span>总 Symbols</span>
            <strong>{items.length}</strong>
          </div>
          <div className="adminMetricTile">
            <span>启用中</span>
            <strong>{items.filter((item) => item.enabled).length}</strong>
          </div>
          <div className="adminMetricTile">
            <span>停用中</span>
            <strong>{items.filter((item) => !item.enabled).length}</strong>
          </div>
          <div className="adminMetricTile">
            <span>当前筛选</span>
            <strong>{filteredItems.length}</strong>
          </div>
        </section>

        <section className="adminSectionCard">
          <div className="adminSectionHeader">
            <div>
              <span className="authEyebrow">Editor</span>
              <h2>{editingId == null ? '新增 Symbol' : `编辑 Symbol #${editingId}`}</h2>
            </div>
            <p>表单保持短列与清晰标签，优先照顾移动端单手操作与状态反馈。</p>
          </div>

          <form className="adminFormGrid" onSubmit={submitForm}>
            <label className="authField">
              <span>Symbol</span>
              <input value={form.symbol} disabled={editingId != null} onChange={(e) => setForm((prev) => ({ ...prev, symbol: e.target.value }))} placeholder="BTCUSDT" />
            </label>
            <label className="authField">
              <span>Base Asset</span>
              <input value={form.base_asset} onChange={(e) => setForm((prev) => ({ ...prev, base_asset: e.target.value }))} placeholder="BTC" />
            </label>
            <label className="authField">
              <span>Quote Asset</span>
              <input value={form.quote_asset} onChange={(e) => setForm((prev) => ({ ...prev, quote_asset: e.target.value }))} placeholder="USDT" />
            </label>
            <label className="authField">
              <span>Timeframe</span>
              <input value={form.timeframe} onChange={(e) => setForm((prev) => ({ ...prev, timeframe: e.target.value }))} placeholder="15m" />
            </label>
            <label className="authField">
              <span>Max Position Size %</span>
              <input value={form.max_position_size_pct} onChange={(e) => setForm((prev) => ({ ...prev, max_position_size_pct: e.target.value }))} placeholder="例如 10" inputMode="decimal" />
            </label>
            <label className="authField">
              <span>Priority</span>
              <input value={form.priority} onChange={(e) => setForm((prev) => ({ ...prev, priority: e.target.value }))} inputMode="numeric" />
            </label>
            <label className="authField">
              <span>Sort Order</span>
              <input value={form.sort_order} onChange={(e) => setForm((prev) => ({ ...prev, sort_order: e.target.value }))} inputMode="numeric" />
            </label>
            <label className="authField adminToggleField">
              <span>状态</span>
              <select value={form.enabled ? 'enabled' : 'disabled'} onChange={(e) => setForm((prev) => ({ ...prev, enabled: e.target.value === 'enabled' }))}>
                <option value="enabled">启用</option>
                <option value="disabled">停用</option>
              </select>
            </label>
            <label className="authField adminFormFull">
              <span>备注</span>
              <input value={form.notes} onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))} placeholder="补充风控阈值、来源说明等" />
            </label>

            {(error || message) && (
              <div className={`adminFormFull ${error ? 'authError' : 'authHint'}`}>
                {error || message}
              </div>
            )}

            <div className="adminHeroActions adminFormFull">
              <button className="shellPrimaryButton" type="submit" disabled={submitting}>
                {submitting ? '提交中…' : editingId == null ? '创建 Symbol' : '保存修改'}
              </button>
              <button className="shellGhostButton" type="button" onClick={startCreate}>
                重置表单
              </button>
            </div>
          </form>
        </section>

        <section className="currencyTableCard">
          <div className="currencyTableHeader">
            <div>
              <h2>Symbol 列表</h2>
              <p>{loading ? '正在加载真实 API 数据…' : '已连接真实 admin symbol API。'}</p>
            </div>
            <span className="currencyCount">{filteredItems.length} / {items.length} 个 Symbols</span>
          </div>

          <div className="currencyTableWrap adminDesktopOnly">
            <table className="currencyTable">
              <thead>
                <tr>
                  <th>币种</th>
                  <th>状态</th>
                  <th>周期</th>
                  <th>仓位上限</th>
                  <th>优先级</th>
                  <th>备注</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>{row.symbol}</strong>
                      <div className="currencyMeta">{row.base_asset}/{row.quote_asset}</div>
                    </td>
                    <td><span className="currencyStatus" data-status={formatStatus(row.enabled)}>{formatStatus(row.enabled)}</span></td>
                    <td>{row.timeframe}</td>
                    <td>{row.max_position_size_pct == null ? '—' : `${row.max_position_size_pct}%`}</td>
                    <td>{row.priority} / {row.sort_order}</td>
                    <td>{row.notes || '—'}</td>
                    <td>
                      <div className="currencyActions">
                        <button className="shellGhostButton" type="button" onClick={() => startEdit(row)}>编辑</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="adminMobileList adminMobileOnly">
            {filteredItems.map((row) => (
              <article key={row.id} className="adminMobileCard adminRecordCard">
                <div className="adminMobileCardHeader">
                  <div>
                    <strong>{row.symbol}</strong>
                    <p>{row.base_asset}/{row.quote_asset} · {row.timeframe}</p>
                  </div>
                  <span className="currencyStatus" data-status={formatStatus(row.enabled)}>{formatStatus(row.enabled)}</span>
                </div>
                <div className="adminMobileMeta">
                  <span>仓位上限：{row.max_position_size_pct == null ? '—' : `${row.max_position_size_pct}%`}</span>
                  <span>优先级：{row.priority}</span>
                  <span>排序：{row.sort_order}</span>
                </div>
                <p className="adminMobileNote">{row.notes || '暂无备注'}</p>
                <div className="currencyActions">
                  <button className="shellGhostButton" type="button" onClick={() => startEdit(row)}>编辑</button>
                </div>
              </article>
            ))}
          </div>

          {!loading && filteredItems.length === 0 && <div className="authHint">当前筛选条件下没有符号配置。</div>}
          {error && !submitting && <div className="authError" style={{ marginTop: 16 }}>{error}</div>}
        </section>
      </main>
    </RouteGuard>
  )
}
