'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useMemo } from 'react'
import { useAuth } from '@/components/auth-provider'

const BASE_NAV_ITEMS = [
  { href: '/', label: '控制台' },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { ready, session, logout } = useAuth()

  const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/register')
  const isAdmin = session?.user.role === 'admin'

  const navItems = useMemo(() => {
    if (!isAdmin) return BASE_NAV_ITEMS
    return [...BASE_NAV_ITEMS, { href: '/admin', label: '管理后台' }]
  }, [isAdmin])

  const userLabel = useMemo(() => {
    if (!session) return '未登录'
    return `${session.user.name} · ${session.user.role === 'admin' ? '管理员' : '普通用户'}`
  }, [session])

  return (
    <>
      <header className="shellHeader">
        <div className="shellBrand">
          <span className="shellLogo">⚡</span>
          <div>
            <strong>AlphaPilot</strong>
            <small>{isAdmin ? 'Control plane · admin ready' : 'Control plane · operator view'}</small>
          </div>
        </div>

        <nav className="shellNav" aria-label="主导航">
          {navItems.map((item) => {
            const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
            return (
              <Link key={item.href} href={item.href} className="shellNavItem" data-active={active}>
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="shellActions">
          <div className="shellUserCard">
            <span className="shellStatusDot" data-ready={ready} />
            <div>
              <strong>{userLabel}</strong>
              <small>{session ? session.user.email : '本地存储会话'}</small>
            </div>
          </div>

          {session ? (
            <>
              {isAdmin && !pathname.startsWith('/admin') && (
                <Link href="/admin" className="shellGhostButton">
                  后台入口
                </Link>
              )}
              <button
                className="shellGhostButton"
                onClick={() => {
                  logout()
                  router.push('/login')
                }}
              >
                退出
              </button>
            </>
          ) : !isAuthPage ? (
            <Link href="/login" className="shellPrimaryButton">
              登录 / 注册
            </Link>
          ) : null}
        </div>
      </header>
      {children}
    </>
  )
}
