'use client'

import Link from 'next/link'
import { RouteGuard } from '@/components/route-guard'

const quickLinks = [
  {
    title: 'Symbol 管理',
    description: '围绕交易 symbol 做筛选、编辑与状态治理，页面语义不再混用 currencies / symbols。',
    href: '/admin/currencies',
    cta: '进入 Symbol 管理',
    tone: 'primary',
  },
  {
    title: '用户与权限',
    description: '已接通 /api/admin/users，可查看用户列表、筛选成员，并调整角色 / 状态。',
    href: '/admin/users',
    cta: '进入用户管理',
    tone: 'neutral',
  },
  {
    title: '审计日志',
    description: '补上管理员操作的时间线骨架，先统一列表结构，再继续增强筛选与详情。',
    href: '/admin/audit-logs',
    cta: '进入审计日志',
    tone: 'neutral',
  },
]

export default function AdminPage() {
  return (
    <RouteGuard requireRole="admin">
      <main className="adminPage">
        <section className="adminHero adminHeroLuxury adminSurfaceGlow">
          <div className="adminHeroSplit">
            <div className="adminHeroContent">
              <span className="authEyebrow">Admin Console</span>
              <h1>AlphaPilot 控制平面</h1>
              <p>统一后台首页、用户管理、Symbol 管理和审计日志的视觉语言：更强信息层级、更清楚的主操作、更适合移动端触达。</p>
              <div className="adminHeroActions">
                <Link href="/admin/currencies" className="shellPrimaryButton">
                  进入 Symbol 管理
                </Link>
                <Link href="/admin/audit-logs" className="shellGhostButton">
                  查看审计日志
                </Link>
              </div>
            </div>
            <div className="adminHighlightCard">
              <span className="adminHighlightLabel">本轮聚焦</span>
              <strong>统一视觉 + 收口语义 + 补日志骨架</strong>
              <p>先把后台做成一套完整的管理体验，再继续补深层联调和细节状态。</p>
            </div>
          </div>
          <div className="adminHeroStats adminHeroStatsDense">
            <div className="adminMetricTile">
              <span>API 状态</span>
              <strong>Auth / Admin 已接通</strong>
            </div>
            <div className="adminMetricTile">
              <span>页面语义</span>
              <strong>Users / Symbols / Audit</strong>
            </div>
            <div className="adminMetricTile">
              <span>交互形态</span>
              <strong>桌面表格 + 移动卡片</strong>
            </div>
            <div className="adminMetricTile">
              <span>联调重点</span>
              <strong>写入口与状态反馈</strong>
            </div>
          </div>
        </section>

        <section className="adminSectionCard">
          <div className="adminSectionHeader">
            <div>
              <span className="authEyebrow">Admin Navigation</span>
              <h2>后台模块</h2>
            </div>
            <p>用统一卡片结构承接导航、状态说明和主操作，减少管理员切页成本。</p>
          </div>
          <div className="adminGrid adminFeatureGrid">
            {quickLinks.map((item) => (
              <article key={item.title} className="adminCard adminFeatureCard" data-tone={item.tone}>
                <span className="adminCardKicker">{item.href.replace('/admin/', '').replace('/', '') || 'overview'}</span>
                <h2>{item.title}</h2>
                <p>{item.description}</p>
                <Link href={item.href} className={item.tone === 'primary' ? 'shellPrimaryButton adminInlineLink' : 'shellGhostButton adminInlineLink'}>
                  {item.cta}
                </Link>
              </article>
            ))}
            <article className="adminCard adminCardWide adminChecklistCard">
              <div>
                <span className="adminCardKicker">Current Progress</span>
                <h2>本轮已落地</h2>
              </div>
              <ul>
                <li>后台首页/用户页/Symbol 页统一为深色玻璃面板 + 高亮摘要卡</li>
                <li>Symbol 管理页文案与入口统一收口到 symbol 语义</li>
                <li>补上审计日志页骨架，包含筛选条、桌面表格、移动卡片</li>
                <li>管理员子导航扩展到首页 / symbols / users / audit logs</li>
              </ul>
            </article>
          </div>
        </section>
      </main>
    </RouteGuard>
  )
}
