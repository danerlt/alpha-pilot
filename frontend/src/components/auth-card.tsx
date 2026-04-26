'use client'

import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { FormEvent, useMemo, useState } from 'react'
import { useAuth } from '@/components/auth-provider'

interface AuthCardProps {
  mode: 'login' | 'register'
}

function sanitizeNextPath(nextPath: string | null) {
  if (!nextPath || !nextPath.startsWith('/')) return null
  if (nextPath.startsWith('//')) return null
  return nextPath
}

export function AuthCard({ mode }: AuthCardProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login, register } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const nextPath = useMemo(() => sanitizeNextPath(searchParams.get('next')), [searchParams])
  // 401 自动登出会带 ?reason=session_expired, 在登录卡上显示提示
  const sessionExpired = mode === 'login' && searchParams.get('reason') === 'session_expired'

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    const form = new FormData(event.currentTarget)
    const email = String(form.get('email') || '').trim()
    const password = String(form.get('password') || '').trim()
    const name = String(form.get('name') || '').trim()

    if (!email || !password) {
      setError('请输入邮箱和密码')
      setSubmitting(false)
      return
    }

    if (password.length < 8) {
      setError('密码至少输入 8 位，和后端规则保持一致')
      setSubmitting(false)
      return
    }

    if (mode === 'register' && !name) {
      setError('请输入显示名称')
      setSubmitting(false)
      return
    }

    try {
      const session = mode === 'login'
        ? await login({ email, password })
        : await register({ name, email, password })

      router.push(nextPath || (session.user.role === 'admin' ? '/admin' : '/'))
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  const title = mode === 'login' ? '登录 AlphaPilot' : '创建 AlphaPilot 账号'
  const subtitle = mode === 'login'
    ? '统一视觉语言后的登录入口：更清晰的层级、更现代的卡片系统、更适合移动端的输入与反馈。'
    : '注册流程保持轻量，但体验升级为同一套控制平面视觉系统，减少从营销页到后台的割裂感。'

  return (
    <section className="authLayout authLayoutModern">
      <div className="authHero authHeroModern">
        <span className="authEyebrow">Modern Control Plane</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>

        <div className="authHeroPanel">
          <div className="authHeroPanelGlow" aria-hidden="true" />
          <div>
            <span className="authHeroPanelLabel">体验升级</span>
            <strong>{mode === 'login' ? '会话恢复、跳转回流、状态反馈' : '创建账号、默认普通用户、后台授权分离'}</strong>
          </div>
          <p>
            {mode === 'login'
              ? '登录后保留 bearer token，刷新页面会自动调用 /api/auth/me 校验会话。'
              : '注册接口仍直接调用后端，管理员角色继续由后台管理页维护，避免前端自行抬权。'}
          </p>
        </div>

        <div className="authFeatureGrid">
          <article className="authFeatureCard">
            <span className="authFeatureKicker">Session</span>
            <strong>真实 JWT 会话</strong>
            <p>登录后刷新不丢状态，管理员进入后台，普通用户进入控制台。</p>
          </article>
          <article className="authFeatureCard">
            <span className="authFeatureKicker">Design</span>
            <strong>统一控制平面语言</strong>
            <p>登录/注册与 admin 首页、Users、Symbols 同步升级成统一暗色玻璃卡片系统。</p>
          </article>
          <article className="authFeatureCard">
            <span className="authFeatureKicker">Mobile</span>
            <strong>移动端优先</strong>
            <p>大按钮、足够触达面积、简化信息密度，手机上也能顺手完成登录与注册。</p>
          </article>
        </div>
      </div>

      <form className="authCard authCardModern" onSubmit={handleSubmit}>
        <div className="authCardHeader">
          <div>
            <span className="authEyebrow">{mode === 'login' ? 'Welcome Back' : 'Create Account'}</span>
            <h2>{mode === 'login' ? '欢迎回来' : '开始使用'}</h2>
          </div>
          <p>
            {mode === 'login'
              ? '输入已有账号进入控制台；如果原本要去受保护页面，登录后会自动跳回。'
              : '注册后默认进入普通用户流转；如需后台权限，请使用已有管理员账号登录。'}
          </p>
        </div>

        {mode === 'register' && (
          <label className="authField">
            <span>显示名称</span>
            <input name="name" placeholder="例如：alpha-admin" autoComplete="nickname" />
          </label>
        )}

        <label className="authField">
          <span>邮箱</span>
          <input name="email" type="email" placeholder="you@alpha-pilot.ai" autoComplete="email" />
        </label>

        <label className="authField">
          <span>密码</span>
          <input name="password" type="password" placeholder="至少 8 位" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
        </label>

        <div className="authMicroGrid">
          <div className="authMicroCard">
            <strong>{mode === 'login' ? '自动跳转' : '默认角色'}</strong>
            <span>{mode === 'login' ? '登录后回到原目标页或默认首页' : '新账号默认是普通用户'}</span>
          </div>
          <div className="authMicroCard">
            <strong>{mode === 'login' ? '安全校验' : '权限边界'}</strong>
            <span>{mode === 'login' ? '刷新时自动校验当前会话' : '管理员权限仍由后台授予'}</span>
          </div>
        </div>

        {mode === 'register' && (
          <div className="authHint">
            当前注册页只创建普通用户；管理员角色由后台管理页维护，避免前端自行抬权。
          </div>
        )}

        {sessionExpired && (
          <div className="authHint">会话已过期或被注销，请重新登录。</div>
        )}

        {nextPath && mode === 'login' && (
          <div className="authHint">登录后将返回：{nextPath}</div>
        )}

        {error && <div className="authError">{error}</div>}

        <button className="shellPrimaryButton authSubmit" type="submit" disabled={submitting}>
          {submitting ? '提交中…' : mode === 'login' ? '登录' : '注册并进入'}
        </button>

        <div className="authFooter">
          {mode === 'login' ? (
            <>
              还没有账号？ <Link href={nextPath ? `/register?next=${encodeURIComponent(nextPath)}` : '/register'}>去注册</Link>
            </>
          ) : (
            <>
              已有账号？ <Link href={nextPath ? `/login?next=${encodeURIComponent(nextPath)}` : '/login'}>去登录</Link>
            </>
          )}
        </div>
      </form>
    </section>
  )
}
