'use client'

import Link from 'next/link'
import { Dot, Icon, fmt, fmtPct } from '@/components/ui'
import styles from './shell.module.css'

export interface NavItem {
  href: string
  label: string
  icon: string
  soon?: boolean
}

export interface AccountSummary {
  total_balance_usdt?: number
  daily_pnl_pct?: number
}

export interface SidebarProps {
  navItems: NavItem[]
  activeHref: string
  account: AccountSummary | null
  engine: 'active' | 'paused' | null
  isAdmin: boolean
  loggedIn: boolean
  userName: string
  userMeta: string
  open: boolean
  onNavigate: () => void
  onLogout: () => void
}

export function Sidebar({
  navItems,
  activeHref,
  account,
  engine,
  isAdmin,
  loggedIn,
  userName,
  userMeta,
  open,
  onNavigate,
  onLogout,
}: SidebarProps) {
  const dailyPct = account?.daily_pnl_pct
  const deltaColor = (dailyPct ?? 0) >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)'

  return (
    <aside className={styles.sidebar} data-open={open ? 'true' : undefined}>
      <div className={styles.brand}>
        <span className={styles.brandMark}>α</span>
        <div>
          <div className={styles.brandName}>
            Alpha<b>Pilot</b>
          </div>
          <div className={styles.brandSub}>AI 自主交易</div>
        </div>
      </div>

      <div className={styles.equity}>
        <div className={styles.equityLabel}>账户权益 · USDT</div>
        <div className={styles.equityValue}>
          {account?.total_balance_usdt != null ? fmt(account.total_balance_usdt) : '—'}
        </div>
        {dailyPct != null && (
          <div className={styles.equityDelta} style={{ color: deltaColor }}>
            {fmtPct(dailyPct * 100)} 今日
          </div>
        )}
      </div>

      <nav className={styles.nav} aria-label="主导航">
        {navItems.map((item) => {
          const active = item.href === '/' ? activeHref === '/' : activeHref.startsWith(item.href)
          if (item.soon) {
            return (
              <div key={item.href} className={styles.navItem} data-soon="true" title="即将上线">
                <Icon name={item.icon} size={16} />
                <span className={styles.navLabel}>{item.label}</span>
                <span className={styles.navSoon}>soon</span>
              </div>
            )
          }
          return (
            <Link
              key={item.href}
              href={item.href}
              className={styles.navItem}
              data-active={active ? 'true' : undefined}
              onClick={onNavigate}
            >
              <Icon name={item.icon} size={16} color={active ? 'var(--ap-mint)' : 'currentColor'} />
              <span className={styles.navLabel}>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <div className={styles.foot}>
        {isAdmin && engine && (
          <div className={styles.engine}>
            <Dot color={engine === 'active' ? 'var(--ap-mint)' : 'var(--ap-rose)'} glow />
            <span>{engine === 'active' ? '引擎运行中' : '引擎已暂停'}</span>
          </div>
        )}
        {loggedIn ? (
          <div className={styles.userRow}>
            <div className={styles.userInfo}>
              <div className={styles.userName}>{userName}</div>
              <div className={styles.userMeta}>{userMeta}</div>
            </div>
            <button className={styles.iconBtn} onClick={onLogout} aria-label="退出登录" title="退出登录">
              <Icon name="logout" size={15} />
            </button>
          </div>
        ) : (
          <Link href="/login" className={styles.navItem} data-active="true" onClick={onNavigate}>
            <Icon name="logout" size={16} color="var(--ap-mint)" />
            <span className={styles.navLabel}>去登录</span>
          </Link>
        )}
      </div>
    </aside>
  )
}
