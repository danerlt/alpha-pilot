/**
 * AlphaPilot UI 组件库 — 方向 A 专业交易终端。
 * 全部基于 --ap-* 设计令牌；数字用 JetBrains Mono + tabular-nums。
 */
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import styles from './ui.module.css'

export { Icon } from './Icon'
export type { IconProps } from './Icon'
export { Modal, ConfirmDialog } from './Modal'
export type { ModalProps, ConfirmDialogProps } from './Modal'

export type Tone = 'mint' | 'rose' | 'amber' | 'violet' | 'cyan' | 'default'

// ---------- Badge / Pill ----------
export function Badge({ tone = 'default', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={styles.badge} data-tone={tone === 'default' ? undefined : tone}>
      {children}
    </span>
  )
}

// ---------- Dot ----------
export function Dot({ color, glow, size = 6 }: { color: string; glow?: boolean; size?: number }) {
  return (
    <span
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: color,
        boxShadow: glow ? `0 0 6px ${color}` : 'none',
        display: 'inline-block',
        flexShrink: 0,
      }}
    />
  )
}

// ---------- Button ----------
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
}
export function Button({ variant = 'default', size = 'md', fullWidth, className, children, ...rest }: ButtonProps) {
  return (
    <button
      className={`${styles.button}${fullWidth ? ' ' + styles.buttonFull : ''}${className ? ' ' + className : ''}`}
      data-variant={variant === 'default' ? undefined : variant}
      data-size={size === 'md' ? undefined : size}
      {...rest}
    >
      {children}
    </button>
  )
}

// ---------- Card ----------
export function Card({
  title,
  right,
  dense,
  glow,
  children,
  className,
  style,
}: {
  title?: ReactNode
  right?: ReactNode
  dense?: boolean
  glow?: boolean
  children: ReactNode
  className?: string
  style?: React.CSSProperties
}) {
  return (
    <div
      className={`${styles.card}${className ? ' ' + className : ''}`}
      data-dense={dense ? 'true' : undefined}
      data-glow={glow ? 'true' : undefined}
      style={style}
    >
      {title && (
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>{title}</div>
          {right}
        </div>
      )}
      <div className={styles.cardBody}>{children}</div>
    </div>
  )
}

// ---------- StatCard ----------
export function StatCard({
  label,
  value,
  sub,
  tone,
  size = 'md',
}: {
  label: ReactNode
  value: ReactNode
  sub?: ReactNode
  tone?: 'pos' | 'neg' | 'ai'
  size?: 'sm' | 'md' | 'lg'
}) {
  return (
    <div className={styles.stat}>
      <div className={styles.statLabel}>{label}</div>
      <div className={styles.statValue} data-tone={tone} data-size={size === 'md' ? undefined : size}>
        {value}
      </div>
      {sub != null && <div className={styles.statSub}>{sub}</div>}
    </div>
  )
}

// ---------- RiskBanner ----------
export function RiskBanner({
  tone = 'pass',
  icon,
  children,
}: {
  tone?: 'pass' | 'degrade' | 'reject' | 'info'
  icon?: ReactNode
  children: ReactNode
}) {
  return (
    <div className={styles.riskBanner} data-tone={tone === 'info' ? undefined : tone}>
      {icon}
      <div style={{ flex: 1 }}>{children}</div>
    </div>
  )
}

// ---------- Table ----------
export const numClass = styles.num
export function Table({ children }: { children: ReactNode }) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>{children}</table>
    </div>
  )
}

// ---------- Sparkline ----------
export function Sparkline({
  data,
  width = 400,
  height = 110,
  color = 'var(--ap-mint)',
  fill = true,
  gradientId = 'ap-spark',
}: {
  data: number[]
  width?: number
  height?: number
  color?: string
  fill?: boolean
  gradientId?: string
}) {
  if (!data || data.length < 2) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const pts = data.map((v, i) => [(i / (data.length - 1)) * width, height - ((v - min) / range) * (height - 8) - 4])
  const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')
  const area = `${path} L ${width} ${height} L 0 ${height} Z`
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ display: 'block' }}>
      <defs>
        <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.35" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={area} fill={`url(#${gradientId})`} />}
      <path d={path} stroke={color} strokeWidth="1.8" fill="none" strokeLinejoin="round" />
    </svg>
  )
}

// ---------- 数字 / 时间格式化 ----------
export const fmt = (n: number, d = 2) =>
  n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
export const fmtPct = (n: number) => (n >= 0 ? '+' : '') + n.toFixed(2) + '%'
export const fmtSigned = (n: number) =>
  (n >= 0 ? '+' : '−') + '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const fmtTime = (iso: string) => new Date(iso).toLocaleString('zh-CN', { hour12: false })
export function fmtHolding(seconds: number) {
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  return `${Math.floor(seconds / 86400)}d`
}
