'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Icon, IconName } from '../atoms/Icon'
import { Dot, wfmt, wfmtPct } from '../atoms'

interface NavItem {
  href: string
  label: string
  icon: IconName
  badge?: number
}

const NAV: NavItem[] = [
  { href: '/', label: '主控制台', icon: 'dashboard' },
  { href: '/ai', label: 'AI 决策', icon: 'brain' },
  { href: '/positions', label: '持仓与订单', icon: 'layers' },
  { href: '/performance', label: '回测与绩效', icon: 'chart' },
  { href: '/risk', label: '策略与风控', icon: 'shield' },
  { href: '/audit', label: '审计日志', icon: 'list' },
  { href: '/settings', label: '设置', icon: 'settings' },
]

export interface SidebarProps {
  equity?: number
  equityChangePct?: number
  engineRunning?: boolean
  engineLatencyMs?: number
}

export function Sidebar({
  equity = 0,
  equityChangePct = 0,
  engineRunning = true,
  engineLatencyMs = 0,
}: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      style={{
        width: 240, flexShrink: 0,
        background: 'var(--ap-bg-1)',
        borderRight: '1px solid var(--ap-line)',
        display: 'flex', flexDirection: 'column', height: '100%',
      }}
    >
      {/* brand */}
      <div
        style={{
          padding: '20px 20px 24px', display: 'flex', alignItems: 'center',
          gap: 10, borderBottom: '1px solid var(--ap-line-soft)',
        }}
      >
        <div
          style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, var(--ap-mint) 0%, var(--ap-violet) 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--ap-bg-0)', fontWeight: 800, fontSize: 15,
          }}
        >
          α
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-.01em' }}>
            Alpha<span style={{ color: 'var(--ap-mint)' }}>Pilot</span>
          </div>
          <div style={{ fontSize: 10, color: 'var(--ap-fg-4)', fontFamily: 'var(--ap-font-mono)' }}>
            v0.1
          </div>
        </div>
      </div>

      {/* account summary */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--ap-line-soft)' }}>
        <div
          style={{
            fontSize: 10, color: 'var(--ap-fg-3)',
            letterSpacing: '.08em', textTransform: 'uppercase',
            fontWeight: 500, marginBottom: 6,
          }}
        >
          账户权益
        </div>
        <div
          style={{
            fontFamily: 'var(--ap-font-mono)', fontSize: 20, fontWeight: 700,
            letterSpacing: '-.02em', lineHeight: 1.1,
          }}
        >
          ${wfmt(equity)}
        </div>
        <div
          style={{
            fontFamily: 'var(--ap-font-mono)', fontSize: 11,
            color: equityChangePct >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)',
            marginTop: 3,
          }}
        >
          {wfmtPct(equityChangePct)} 今日
        </div>
      </div>

      {/* nav */}
      <nav
        style={{
          flex: 1, padding: '12px 12px',
          display: 'flex', flexDirection: 'column', gap: 1, overflow: 'auto',
        }}
      >
        {NAV.map((n) => {
          const isActive =
            n.href === '/' ? pathname === '/' : pathname.startsWith(n.href)
          return (
            <Link
              key={n.href}
              href={n.href}
              style={{
                textDecoration: 'none',
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 10px', borderRadius: 8,
                color: isActive ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
                background: isActive ? 'var(--ap-bg-3)' : 'transparent',
                fontSize: 13, fontWeight: 500,
                position: 'relative', transition: '.12s',
              }}
            >
              {isActive && (
                <div
                  style={{
                    position: 'absolute', left: -12, top: 8, bottom: 8,
                    width: 3, borderRadius: 2, background: 'var(--ap-mint)',
                  }}
                />
              )}
              <Icon name={n.icon} size={16} color={isActive ? 'var(--ap-mint)' : 'currentColor'} />
              <span style={{ flex: 1 }}>{n.label}</span>
              {n.badge && (
                <span
                  style={{
                    fontSize: 10, padding: '1px 6px',
                    background: 'var(--ap-violet-soft)', color: 'var(--ap-violet)',
                    borderRadius: 999, fontFamily: 'var(--ap-font-mono)', fontWeight: 600,
                  }}
                >
                  {n.badge}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* engine status */}
      <div
        style={{
          padding: '14px 20px', borderTop: '1px solid var(--ap-line-soft)',
          display: 'flex', flexDirection: 'column', gap: 8,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Dot c={engineRunning ? 'var(--ap-mint)' : 'var(--ap-rose)'} glow />
          <span style={{ fontSize: 11, color: 'var(--ap-fg-2)', fontWeight: 500 }}>
            {engineRunning ? '引擎运行中' : '引擎停止'}
          </span>
          <span
            style={{
              marginLeft: 'auto', fontSize: 10, color: 'var(--ap-fg-4)',
              fontFamily: 'var(--ap-font-mono)',
            }}
          >
            {engineLatencyMs}ms
          </span>
        </div>
        <div style={{ fontSize: 10, color: 'var(--ap-fg-4)', fontFamily: 'var(--ap-font-mono)' }}>
          Binance · testnet
        </div>
      </div>
    </aside>
  )
}
