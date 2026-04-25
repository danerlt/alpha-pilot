'use client'

import * as React from 'react'
import { Icon } from '../atoms/Icon'
import { Dot, wfmtPct } from '../atoms'

export interface TopbarProps {
  pageTitle: string
  pageSub?: string
  riskState?: 'OK' | 'WARN' | 'HALTED'
  regime?: string
  positionsPct?: number
  dayLossPct?: number
  autoOn?: boolean
}

export function Topbar({
  pageTitle, pageSub,
  riskState = 'OK',
  regime = 'unknown',
  positionsPct = 0,
  dayLossPct = 0,
  autoOn = true,
}: TopbarProps) {
  const riskCfg = {
    OK: { c: 'var(--ap-mint)', label: '风控正常' },
    WARN: { c: 'var(--ap-amber)', label: '接近阈值' },
    HALTED: { c: 'var(--ap-rose)', label: '已熔断' },
  }[riskState]

  return (
    <header
      style={{
        display: 'flex', alignItems: 'center', gap: 16,
        padding: '14px 24px',
        borderBottom: '1px solid var(--ap-line-soft)',
        background: 'var(--ap-bg-1)',
        height: 60, boxSizing: 'border-box',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        {pageSub && (
          <div
            style={{
              fontSize: 10, color: 'var(--ap-fg-3)',
              letterSpacing: '.08em', textTransform: 'uppercase',
              fontWeight: 500, marginBottom: 1,
            }}
          >
            {pageSub}
          </div>
        )}
        <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-.01em' }}>
          {pageTitle}
        </div>
      </div>

      {/* risk status chip */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '6px 12px', background: 'var(--ap-bg-2)',
          borderRadius: 999, border: '1px solid var(--ap-line-soft)',
        }}
      >
        <Dot c={riskCfg.c} glow />
        <span style={{ fontSize: 12, fontWeight: 600, color: riskCfg.c }}>
          {riskCfg.label}
        </span>
        <span
          style={{
            fontSize: 11, color: 'var(--ap-fg-3)',
            fontFamily: 'var(--ap-font-mono)',
          }}
        >
          仓位 {positionsPct}% · 日损 {wfmtPct(dayLossPct)} · {regime}
        </span>
      </div>

      {/* search */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 10px 6px 12px',
          background: 'var(--ap-bg-2)', borderRadius: 8,
          border: '1px solid var(--ap-line-soft)', cursor: 'pointer',
          width: 260,
        }}
      >
        <Icon name="search" size={14} color="var(--ap-fg-3)" />
        <span style={{ fontSize: 12, color: 'var(--ap-fg-4)', flex: 1 }}>
          搜索交易对、决策、策略…
        </span>
        <span
          style={{
            fontFamily: 'var(--ap-font-mono)', fontSize: 10,
            color: 'var(--ap-fg-4)', background: 'var(--ap-bg-3)',
            padding: '2px 6px', borderRadius: 4,
            border: '1px solid var(--ap-line)',
          }}
        >
          ⌘K
        </span>
      </div>

      {/* bell */}
      <button
        style={{
          width: 34, height: 34, borderRadius: 8,
          background: 'var(--ap-bg-2)', border: '1px solid var(--ap-line-soft)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', color: 'var(--ap-fg-2)', position: 'relative',
        }}
      >
        <Icon name="bell" size={15} />
      </button>

      {/* auto switch */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 12px',
          background: autoOn ? 'var(--ap-mint-soft)' : 'var(--ap-bg-3)',
          borderRadius: 8,
          border: `1px solid ${autoOn ? 'rgba(0,211,149,.25)' : 'var(--ap-line)'}`,
        }}
      >
        <Dot c={autoOn ? 'var(--ap-mint)' : 'var(--ap-fg-4)'} glow={autoOn} />
        <span
          style={{
            fontSize: 12, fontWeight: 600,
            color: autoOn ? 'var(--ap-mint)' : 'var(--ap-fg-3)',
            fontFamily: 'var(--ap-font-mono)',
          }}
        >
          {autoOn ? 'AUTO' : 'PAUSED'}
        </span>
      </div>
    </header>
  )
}
