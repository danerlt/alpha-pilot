import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { Badge, Button, Card, RiskBanner, Sparkline, StatCard, fmt, fmtPct, fmtSigned, fmtHolding } from './index'
import { ConfirmDialog } from './Modal'

describe('UI atoms', () => {
  it('Badge 渲染文案与色调', () => {
    const html = renderToStaticMarkup(<Badge tone="mint">PASS</Badge>)
    expect(html).toContain('PASS')
    expect(html).toContain('data-tone="mint"')
  })

  it('Button 渲染 variant 与 disabled', () => {
    const html = renderToStaticMarkup(
      <Button variant="danger" disabled>
        平仓
      </Button>,
    )
    expect(html).toContain('平仓')
    expect(html).toContain('data-variant="danger"')
    expect(html).toContain('disabled')
  })

  it('StatCard 渲染 label/value/tone', () => {
    const html = renderToStaticMarkup(<StatCard label="今日盈亏" value="+182.44" tone="pos" />)
    expect(html).toContain('今日盈亏')
    expect(html).toContain('+182.44')
    expect(html).toContain('data-tone="pos"')
  })

  it('Card 渲染标题与内容', () => {
    const html = renderToStaticMarkup(<Card title="当前持仓">body-content</Card>)
    expect(html).toContain('当前持仓')
    expect(html).toContain('body-content')
  })

  it('RiskBanner 渲染色调与内容', () => {
    const html = renderToStaticMarkup(<RiskBanner tone="reject">守卫拒绝</RiskBanner>)
    expect(html).toContain('守卫拒绝')
    expect(html).toContain('data-tone="reject"')
  })

  it('Sparkline 数据足够时渲染 svg path', () => {
    const html = renderToStaticMarkup(<Sparkline data={[1, 2, 3, 2, 4]} />)
    expect(html).toContain('<svg')
    expect(html).toContain('<path')
  })

  it('Sparkline 数据不足返回空', () => {
    const html = renderToStaticMarkup(<Sparkline data={[1]} />)
    expect(html).toBe('')
  })
})

describe('ConfirmDialog', () => {
  it('open=false 不渲染', () => {
    const html = renderToStaticMarkup(
      <ConfirmDialog open={false} title="t" message="m" onConfirm={() => {}} onCancel={() => {}} />,
    )
    expect(html).toBe('')
  })

  it('open=true 渲染标题与消息', () => {
    const html = renderToStaticMarkup(
      <ConfirmDialog open title="一键平仓" message="确认全平？" onConfirm={() => {}} onCancel={() => {}} />,
    )
    expect(html).toContain('一键平仓')
    expect(html).toContain('确认全平？')
  })

  it('requireText 时渲染口令输入框且确认按钮初始禁用', () => {
    const html = renderToStaticMarkup(
      <ConfirmDialog
        open
        title="高危"
        message="m"
        tone="danger"
        requireText="CLOSE ALL"
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    )
    expect(html).toContain('CLOSE ALL')
    expect(html).toContain('disabled')
  })
})

describe('格式化helpers', () => {
  it('fmt 千分位两位小数', () => {
    expect(fmt(12480.5)).toBe('12,480.50')
  })
  it('fmtPct 带符号两位小数', () => {
    expect(fmtPct(1.48)).toBe('+1.48%')
    expect(fmtPct(-0.62)).toBe('-0.62%')
  })
  it('fmtSigned 负数用 − 前缀', () => {
    expect(fmtSigned(-36.8)).toBe('−$36.80')
  })
  it('fmtHolding 人类可读时长', () => {
    expect(fmtHolding(120)).toBe('2m')
    expect(fmtHolding(3720)).toBe('1h 2m')
    expect(fmtHolding(90000)).toBe('1d')
  })
})
