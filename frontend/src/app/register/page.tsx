import Link from 'next/link'

// V0.1 单管理员场景下公开注册已禁用 (post-Plan5 安全审计 C5).
// 后端 POST /api/auth/register 也直接返 403, 这个页面只显示提示, 不再
// 走 AuthCard mode='register' 的真实注册流程.
export default function RegisterPage() {
  return (
    <section className="authLayout authLayoutModern">
      <div className="authHero authHeroModern">
        <span className="authEyebrow">Registration disabled</span>
        <h1>注册已关闭</h1>
        <p>
          AlphaPilot V0.1 不开放公开注册。如需账号请联系系统管理员通过后台管理页
          (/admin/users) 创建。
        </p>
        <div className="authHeroPanel">
          <Link href="/login" className="shellPrimaryButton">回到登录</Link>
        </div>
      </div>
    </section>
  )
}
