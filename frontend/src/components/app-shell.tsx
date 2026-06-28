'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { AdminSubnav } from '@/components/admin-subnav'
import { useAuth } from '@/components/auth-provider'
import { fmtPct } from '@/components/ui'
import { apiRequest, buildAuthHeaders, getKillSwitch } from '@/lib/api'
import { Sidebar, type AccountSummary, type NavItem } from '@/components/shell/Sidebar'
import { Topbar, type RiskChip } from '@/components/shell/Topbar'
import styles from '@/components/shell/shell.module.css'

const BASE_NAV: NavItem[] = [
  { href: '/', label: '主控制台', icon: 'dashboard' },
  { href: '/decisions', label: 'AI 决策流', icon: 'brain', soon: true },
  { href: '/positions', label: '持仓与订单', icon: 'layers', soon: true },
  { href: '/performance', label: '交易与绩效', icon: 'chart', soon: true },
  { href: '/strategy', label: '策略与风控', icon: 'shield', soon: true },
  { href: '/insights', label: '归因与审计', icon: 'scroll-text', soon: true },
]
const SETTINGS_NAV: NavItem = { href: '/settings', label: '设置', icon: 'settings', soon: true }
const ADMIN_NAV: NavItem = { href: '/admin', label: '管理后台', icon: 'shield-alert' }

function pageMeta(pathname: string): { title: string; sub: string } {
  if (pathname === '/') return { title: '主控制台', sub: 'COCKPIT' }
  if (pathname.startsWith('/admin/users')) return { title: '用户管理', sub: 'ADMIN' }
  if (pathname.startsWith('/admin/audit-logs')) return { title: '审计日志', sub: 'ADMIN' }
  if (pathname.startsWith('/admin/currencies')) return { title: '交易对管理', sub: 'ADMIN' }
  if (pathname.startsWith('/admin')) return { title: '管理后台', sub: 'ADMIN' }
  return { title: 'AlphaPilot', sub: '' }
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { session, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [account, setAccount] = useState<AccountSummary | null>(null)
  const [engine, setEngine] = useState<'active' | 'paused' | null>(null)
  const [unresolved, setUnresolved] = useState(0)

  const token = session?.token
  const isAdmin = session?.user.role === 'admin'
  const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/register')

  useEffect(() => {
    if (!token) {
      setAccount(null)
      setEngine(null)
      setUnresolved(0)
      return
    }
    let cancelled = false
    const load = async () => {
      const [acc, risks, ks] = await Promise.all([
        apiRequest<AccountSummary>('/account', { headers: buildAuthHeaders(token) }).catch(() => null),
        apiRequest<{ resolved: boolean }[]>('/risk-events?limit=50', { headers: buildAuthHeaders(token) }).catch(() => []),
        isAdmin ? getKillSwitch(token).then((r) => r.state).catch(() => null) : Promise.resolve(null),
      ])
      if (cancelled) return
      setAccount(acc)
      setUnresolved((risks || []).filter((r) => !r.resolved).length)
      setEngine(ks)
    }
    load()
    const t = setInterval(load, 30000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [token, isAdmin])

  const navItems = useMemo(() => {
    const items = [...BASE_NAV]
    if (isAdmin) items.push(ADMIN_NAV)
    items.push(SETTINGS_NAV)
    return items
  }, [isAdmin])

  const handleLogout = useCallback(() => {
    logout()
    router.push('/login')
  }, [logout, router])

  const closeDrawer = useCallback(() => setOpen(false), [])

  if (isAuthPage) {
    return <>{children}</>
  }

  const { title, sub } = pageMeta(pathname)
  const dailyPct = account?.daily_pnl_pct
  const detail = dailyPct != null ? `日盈亏 ${fmtPct(dailyPct * 100)}` : undefined

  let riskChip: RiskChip | null = null
  if (session) {
    if (isAdmin && engine === 'paused') riskChip = { tone: 'rose', label: '已暂停', detail }
    else if (unresolved > 0) riskChip = { tone: 'amber', label: `风控事件 ${unresolved}`, detail }
    else riskChip = { tone: 'mint', label: '风控正常', detail }
  }

  const userName = session ? session.user.name : '未登录'
  const userMeta = session ? `${session.user.email} · ${isAdmin ? '管理员' : '普通用户'}` : '本地存储会话'

  return (
    <div className={styles.shell}>
      <div className={styles.backdrop} data-open={open ? 'true' : undefined} onClick={closeDrawer} />
      <Sidebar
        navItems={navItems}
        activeHref={pathname}
        account={account}
        engine={engine}
        isAdmin={!!isAdmin}
        loggedIn={!!session}
        userName={userName}
        userMeta={userMeta}
        open={open}
        onNavigate={closeDrawer}
        onLogout={handleLogout}
      />
      <div className={styles.main}>
        <Topbar
          title={title}
          sub={sub}
          riskChip={riskChip}
          autoState={isAdmin ? engine : null}
          unresolvedCount={unresolved}
          onMenu={() => setOpen(true)}
        />
        {isAdmin && pathname.startsWith('/admin') && <AdminSubnav />}
        <main>{children}</main>
      </div>
    </div>
  )
}
