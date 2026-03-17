'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const adminNavItems = [
  { href: '/admin', label: '后台首页' },
  { href: '/admin/currencies', label: 'Symbol 管理' },
  { href: '/admin/users', label: '用户管理' },
  { href: '/admin/audit-logs', label: '审计日志' },
]

export function AdminSubnav() {
  const pathname = usePathname()

  return (
    <nav className="adminSubnav" aria-label="后台子导航">
      {adminNavItems.map((item) => {
        const active = item.href === '/admin' ? pathname === item.href : pathname.startsWith(item.href)
        return (
          <Link key={item.href} href={item.href} className="adminSubnavItem" data-active={active}>
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}
