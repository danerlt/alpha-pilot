'use client'

/**
 * Dashboard preview — DS Web Shell + 关键卡片的最小可访问版本.
 *
 * 路由 `/preview/dashboard` 与既有 / page.tsx 并存; V0.2 把 7 页重做后
 * 再切换主路由。本页用 AppShell + Card + Stat + Spark 展示账户/持仓/决策概览.
 */

import * as React from 'react'
import { AppShell } from '@/components/ds/shell/AppShell'
import { Card, Pill, Spark, Stat, wfmt, wfmtPct } from '@/components/ds/atoms'
import { Icon } from '@/components/ds/atoms/Icon'

interface DashboardData {
  equity: number
  equityChangePct: number
  todayPnl: number
  todayPnlPct: number
  weekPnl: number
  weekPnlPct: number
  positions: number
  positionsPct: number
  dayLossPct: number
  riskState: 'OK' | 'WARN' | 'HALTED'
  regime: string
  equitySpark: number[]
  recentDecisions: Array<{
    id: string
    time: string
    symbol: string
    action: 'OPEN_LONG' | 'CLOSE_LONG' | 'HOLD'
    guard: 'PASS' | 'REJECT' | 'DEGRADE'
    isFallback: boolean
  }>
}

// 占位 mock 数据; 真实数据接通 lib/api 后替换
const MOCK_DATA: DashboardData = {
  equity: 128450.73,
  equityChangePct: 1.82,
  todayPnl: 1248.05,
  todayPnlPct: 0.98,
  weekPnl: 5420.11,
  weekPnlPct: 4.32,
  positions: 2,
  positionsPct: 12,
  dayLossPct: -0.48,
  riskState: 'OK',
  regime: 'trending_up',
  equitySpark: [120000, 121000, 119500, 122500, 124000, 123500, 126000, 128450],
  recentDecisions: [
    { id: 'd_1', time: '14:23:08', symbol: 'BTCUSDT', action: 'OPEN_LONG', guard: 'PASS', isFallback: false },
    { id: 'd_2', time: '13:45:00', symbol: 'ETHUSDT', action: 'HOLD', guard: 'DEGRADE', isFallback: false },
    { id: 'd_3', time: '12:30:00', symbol: 'BTCUSDT', action: 'OPEN_LONG', guard: 'REJECT', isFallback: false },
    { id: 'd_4', time: '10:15:00', symbol: 'BTCUSDT', action: 'CLOSE_LONG', guard: 'PASS', isFallback: false },
    { id: 'd_5', time: '09:02:00', symbol: 'ETHUSDT', action: 'OPEN_LONG', guard: 'PASS', isFallback: false },
  ],
}

function actionTone(action: 'OPEN_LONG' | 'CLOSE_LONG' | 'HOLD') {
  if (action === 'OPEN_LONG') return 'mint' as const
  if (action === 'CLOSE_LONG') return 'cyan' as const
  return 'default' as const
}

function guardTone(g: 'PASS' | 'REJECT' | 'DEGRADE') {
  if (g === 'PASS') return 'mint' as const
  if (g === 'REJECT') return 'rose' as const
  return 'amber' as const
}

export default function DashboardPreviewPage() {
  const data = MOCK_DATA

  return (
    <AppShell
      pageTitle="主控制台"
      pageSub="Dashboard"
      sidebar={{
        equity: data.equity,
        equityChangePct: data.equityChangePct,
        engineRunning: true,
        engineLatencyMs: 48,
      }}
      topbar={{
        riskState: data.riskState,
        regime: data.regime,
        positionsPct: data.positionsPct,
        dayLossPct: data.dayLossPct,
        autoOn: true,
      }}
    >
      {/* 顶部关键指标 */}
      <div
        style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16, marginBottom: 16,
        }}
      >
        <Card title="账户权益" dense>
          <Stat
            label=""
            value={`$${wfmt(data.equity)}`}
            sub={
              <span style={{ color: data.equityChangePct >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)' }}>
                {wfmtPct(data.equityChangePct)} 今日
              </span>
            }
            size="lg"
            tone="default"
          />
        </Card>
        <Card title="今日盈亏" dense>
          <Stat
            label=""
            value={`${data.todayPnl >= 0 ? '+' : '−'}$${wfmt(Math.abs(data.todayPnl))}`}
            sub={wfmtPct(data.todayPnlPct)}
            size="lg"
            tone={data.todayPnl >= 0 ? 'pos' : 'neg'}
          />
        </Card>
        <Card title="本周盈亏" dense>
          <Stat
            label=""
            value={`${data.weekPnl >= 0 ? '+' : '−'}$${wfmt(Math.abs(data.weekPnl))}`}
            sub={wfmtPct(data.weekPnlPct)}
            size="lg"
            tone={data.weekPnl >= 0 ? 'pos' : 'neg'}
          />
        </Card>
        <Card title="持仓" dense>
          <Stat
            label=""
            value={String(data.positions)}
            sub={`占用 ${data.positionsPct}%`}
            size="lg"
          />
        </Card>
      </div>

      {/* 权益曲线 */}
      <Card title="权益走势" right={<Pill tone="cyan">7d</Pill>} style={{ marginBottom: 16 }}>
        <Spark data={data.equitySpark} width={760} height={120} />
      </Card>

      {/* 最近 AI 决策 */}
      <Card
        title="最近 AI 决策"
        right={<Pill tone="violet">VIOLET = AI</Pill>}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {data.recentDecisions.map((d) => (
            <div
              key={d.id}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '8px 10px', background: 'var(--ap-bg-3)',
                borderRadius: 8,
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--ap-font-mono)', fontSize: 11,
                  color: 'var(--ap-fg-3)', minWidth: 60,
                }}
              >
                {d.time}
              </span>
              <span
                style={{
                  fontWeight: 600, fontSize: 13, minWidth: 80,
                  color: 'var(--ap-fg-1)',
                }}
              >
                {d.symbol}
              </span>
              <Pill tone={actionTone(d.action)}>{d.action}</Pill>
              <Pill tone={guardTone(d.guard)}>{d.guard}</Pill>
              {d.isFallback && <Pill tone="amber">FALLBACK</Pill>}
              <span style={{ flex: 1 }} />
              <Icon name="chevron_right" size={14} color="var(--ap-fg-4)" />
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  )
}
