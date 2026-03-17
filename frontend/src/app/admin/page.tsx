'use client'

import Link from 'next/link'
import { RouteGuard } from '@/components/route-guard'

const quickLinks = [
  {
    title: '符号管理',
    description: '已接通 /api/admin/symbols，可查看、筛选、新增与编辑交易符号配置。',
    href: '/admin/currencies',
    cta: '进入符号管理',
  },
  {
    title: '用户与权限',
    description: '已接通 /api/admin/users，可查看用户列表并调整角色 / 状态。',
    href: '/admin/users',
    cta: '进入用户管理',
  },
  {
    title: '系统配置',
    description: '运行时配置仍保留在主控制台，但写入口继续仅向管理员暴露。',
    href: '/',
    cta: '回到控制台查看',
  },
]

export default function AdminPage() {
  return (
    <RouteGuard requireRole="admin">
      <main className="adminPage">
        <section className="adminHero adminHeroLuxury">
          <span className="authEyebrow">Admin Console</span>
          <h1>AlphaPilot 控制平面</h1>
          <p>把用户、符号配置和后续审计能力收进一套更清晰的后台体验里。现在先做到：更像产品，不像裸表单。</p>
          <div className="adminHeroActions">
            <Link href="/admin/currencies" className="shellPrimaryButton">
              符号管理
            </Link>
            <Link href="/admin/users" className="shellGhostButton">
              用户管理
            </Link>
          </div>
          <div className="adminHeroStats">
            <div className="adminMetricTile">
              <span>API 状态</span>
              <strong>Auth / Admin 已接通</strong>
            </div>
            <div className="adminMetricTile">
              <span>后台形态</span>
              <strong>桌面表格 + 移动卡片</strong>
            </div>
            <div className="adminMetricTile">
              <span>当前目标</span>
              <strong>联调与审计页收口</strong>
            </div>
          </div>
        </section>

        <section className="adminSectionCard">
          <div className="adminSectionHeader">
            <div>
              <span className="authEyebrow">Admin Navigation</span>
              <h2>后台模块导航</h2>
            </div>
            <p>把入口、状态说明和高频操作收拢，避免管理员在手机上找不到关键页面。</p>
          </div>
          <div className="adminGrid">
            {quickLinks.map((item) => (
              <article key={item.title} className="adminCard">
                <h2>{item.title}</h2>
                <p>{item.description}</p>
                <Link href={item.href} className="shellGhostButton adminInlineLink">
                  {item.cta}
                </Link>
              </article>
            ))}
            <article className="adminCard adminCardWide">
              <h2>本轮已落地</h2>
              <ul>
                <li>登录态切到真实后端 JWT，会话刷新时自动调用 `/api/auth/me` 校验</li>
                <li>符号管理页直接对接 `GET/POST/PATCH /api/admin/symbols`</li>
                <li>用户管理页直接对接 `GET/PATCH /api/admin/users`</li>
                <li>桌面保留表格，移动端切成卡片，避免横向挤压</li>
              </ul>
            </article>
          </div>
        </section>
      </main>
    </RouteGuard>
  )
}
