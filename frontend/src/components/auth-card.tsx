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
    ? '优先走真实后端 JWT 登录，管理员登录后可直接进入后台 API 页面。'
    : '注册现在直接调用后端接口，默认创建普通用户账号。管理员权限仍需由后台已有管理员授予。'

  return (
    <section className="authLayout">
      <div className="authHero">
        <span className="authEyebrow">Frontend First / API Wired</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
        <ul>
          <li>登录后保留 bearer token，页面刷新后会自动校验当前会话</li>
          <li>普通用户默认落到控制台，管理员账号落到后台</li>
          <li>后台列表与编辑现在直接请求真实 admin API</li>
        </ul>
      </div>

      <form className="authCard" onSubmit={handleSubmit}>
        <div>
          <h2>{mode === 'login' ? '欢迎回来' : '开始使用'}</h2>
          <p>
            {mode === 'login'
              ? '输入已存在账号进入控制台；如果原本要去受保护页面，登录后会自动跳回。'
              : '注册接口会创建普通用户；若要进入后台，请使用已有管理员账号登录。'}
          </p>
        </div>

        {mode === 'register' && (
          <label className="authField">
            <span>显示名称</span>
            <input name="name" placeholder="例如：alpha-admin" />
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

        {mode === 'register' && (
          <div className="authHint">
            当前注册页只创建普通用户；管理员角色由后台管理页维护，避免前端自行抬权。
          </div>
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
