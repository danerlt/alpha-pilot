'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useAuth } from '@/components/auth-provider'
import { UserRole } from '@/lib/auth'

interface RouteGuardProps {
  children: React.ReactNode
  requireRole?: UserRole
}

export function RouteGuard({ children, requireRole }: RouteGuardProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { ready, session } = useAuth()

  useEffect(() => {
    if (!ready) return
    if (!session) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`)
    }
  }, [pathname, ready, router, session])

  if (!ready) {
    return (
      <main className="marketingPage">
        <section className="marketingHero">
          <span className="authEyebrow">Route Guard</span>
          <h1>正在检查登录态…</h1>
        </section>
      </main>
    )
  }

  if (!session) {
    return (
      <main className="marketingPage">
        <section className="marketingHero">
          <span className="authEyebrow">Need Login</span>
          <h1>此页面需要先登录</h1>
        </section>
      </main>
    )
  }

  if (requireRole && session.user.role !== requireRole) {
    return (
      <main className="marketingPage">
        <section className="marketingHero">
          <span className="authEyebrow">Access Limited</span>
          <h1>当前账号不是管理员</h1>
          <p>前端入口已收口，真正的写操作也会继续被服务端 admin 权限校验拦住。</p>
          <div className="adminHeroActions">
            <Link href="/login" className="shellPrimaryButton">切换管理员账号</Link>
            <Link href="/" className="shellGhostButton">返回控制台</Link>
          </div>
        </section>
      </main>
    )
  }

  return <>{children}</>
}
