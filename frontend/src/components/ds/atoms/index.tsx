'use client'

/**
 * DS atoms — Card / Stat / Pill / Dot / Spark.
 * 从 AlphaPilot Design System/ui_kits/web_app/components/shell.jsx 抽出, 转 TypeScript。
 */
import * as React from 'react'

type Tone = 'mint' | 'rose' | 'amber' | 'violet' | 'cyan' | 'default'

const TONE_BG: Record<Tone, { bg: string; c: string }> = {
  mint: { bg: 'var(--ap-mint-soft)', c: 'var(--ap-mint)' },
  rose: { bg: 'var(--ap-rose-soft)', c: 'var(--ap-rose)' },
  amber: { bg: 'var(--ap-amber-soft)', c: 'var(--ap-amber)' },
  violet: { bg: 'var(--ap-violet-soft)', c: 'var(--ap-violet)' },
  cyan: { bg: 'var(--ap-cyan-soft)', c: 'var(--ap-cyan)' },
  default: { bg: 'var(--ap-bg-3)', c: 'var(--ap-fg-2)' },
}

// ---- Pill -----------------------------------------------------------------
export interface PillProps {
  children: React.ReactNode
  tone?: Tone
}

export function Pill({ children, tone = 'default' }: PillProps) {
  const s = TONE_BG[tone]
  return (
    <span
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        fontSize: 10.5, padding: '2px 8px', borderRadius: 999,
        background: s.bg, color: s.c, fontWeight: 600,
        fontFamily: 'var(--ap-font-mono)', letterSpacing: '.04em',
      }}
    >
      {children}
    </span>
  )
}

// ---- Dot -----------------------------------------------------------------
export interface DotProps {
  c?: string
  glow?: boolean
  size?: number
}

export function Dot({ c = 'var(--ap-mint)', glow = false, size = 6 }: DotProps) {
  return (
    <span
      style={{
        width: size, height: size, borderRadius: '50%',
        background: c, boxShadow: glow ? `0 0 6px ${c}` : 'none',
        display: 'inline-block', flexShrink: 0,
      }}
    />
  )
}

// ---- Card -----------------------------------------------------------------
export interface CardProps {
  children: React.ReactNode
  title?: React.ReactNode
  right?: React.ReactNode
  dense?: boolean
  glow?: boolean
  style?: React.CSSProperties
}

export function Card({ children, style, title, right, dense, glow }: CardProps) {
  return (
    <div
      style={{
        background: 'var(--ap-bg-2)',
        borderRadius: 'var(--ap-r-md)',
        border: '1px solid var(--ap-line-soft)',
        overflow: 'hidden',
        ...(glow ? { boxShadow: '0 0 0 1px var(--ap-violet), 0 0 40px rgba(124,92,255,.12)' } : {}),
        ...style,
      }}
    >
      {title && (
        <div
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: dense ? '10px 14px' : '14px 18px',
            borderBottom: '1px solid var(--ap-line-soft)',
          }}
        >
          <div
            style={{
              fontSize: 11, color: 'var(--ap-fg-3)',
              letterSpacing: '.08em', textTransform: 'uppercase', fontWeight: 600,
            }}
          >
            {title}
          </div>
          {right}
        </div>
      )}
      <div style={{ padding: dense ? '12px 14px' : '16px 18px' }}>{children}</div>
    </div>
  )
}

// ---- Stat -----------------------------------------------------------------
export interface StatProps {
  label: string
  value: React.ReactNode
  sub?: React.ReactNode
  tone?: 'pos' | 'neg' | 'ai' | 'default'
  size?: 'sm' | 'md' | 'lg'
}

export function Stat({ label, value, sub, tone = 'default', size = 'md' }: StatProps) {
  const fs = size === 'lg' ? 28 : size === 'sm' ? 16 : 22
  const colorMap = {
    pos: 'var(--ap-mint)',
    neg: 'var(--ap-rose)',
    ai: 'var(--ap-violet)',
    default: 'var(--ap-fg-1)',
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div
        style={{
          fontSize: 10.5, color: 'var(--ap-fg-3)',
          letterSpacing: '.08em', textTransform: 'uppercase', fontWeight: 500,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: 'var(--ap-font-mono)', fontSize: fs, fontWeight: 700,
          letterSpacing: '-.02em', color: colorMap[tone], lineHeight: 1.1,
        }}
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11.5, color: 'var(--ap-fg-3)', fontFamily: 'var(--ap-font-mono)' }}>
          {sub}
        </div>
      )}
    </div>
  )
}

// ---- Sparkline -----------------------------------------------------------
export interface SparkProps {
  data: number[]
  width?: number
  height?: number
  color?: string
  fill?: boolean
  gradId?: string
}

export function Spark({
  data, width = 400, height = 110,
  color = 'var(--ap-mint)', fill = true, gradId = 'spk',
}: SparkProps) {
  if (!data || data.length === 0) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const r = max - min || 1
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * width,
    height - ((v - min) / r) * (height - 8) - 4,
  ])
  const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')
  const area = path + ` L ${width} ${height} L 0 ${height} Z`
  return (
    <svg
      width={width}
      height={height}
      style={{ display: 'block' }}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={gradId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity=".35" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={area} fill={`url(#${gradId})`} />}
      <path d={path} stroke={color} strokeWidth="1.8" fill="none" strokeLinejoin="round" />
    </svg>
  )
}

// ---- Format helpers ------------------------------------------------------
export const wfmt = (n: number, d: number = 2) =>
  n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })

export const wfmtPct = (n: number) => (n >= 0 ? '+' : '') + n.toFixed(2) + '%'

export const wfmtSigned = (n: number) =>
  (n >= 0 ? '+' : '−') + '$' + Math.abs(n).toLocaleString('en-US', {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  })
