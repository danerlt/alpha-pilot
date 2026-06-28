'use client'

import { Dot, Icon } from '@/components/ui'
import styles from './shell.module.css'

export interface RiskChip {
  tone: 'mint' | 'amber' | 'rose'
  label: string
  detail?: string
}

export interface TopbarProps {
  title: string
  sub: string
  riskChip: RiskChip | null
  autoState: 'active' | 'paused' | null
  unresolvedCount: number
  onMenu: () => void
}

const TONE_COLOR: Record<RiskChip['tone'], string> = {
  mint: 'var(--ap-mint)',
  amber: 'var(--ap-amber)',
  rose: 'var(--ap-rose)',
}

export function Topbar({ title, sub, riskChip, autoState, unresolvedCount, onMenu }: TopbarProps) {
  return (
    <header className={styles.topbar}>
      <button className={`${styles.iconBtn} ${styles.menuBtn}`} onClick={onMenu} aria-label="打开菜单">
        <Icon name="menu" size={18} />
      </button>

      <div className={styles.titleWrap}>
        {sub && <div className={styles.titleSub}>{sub}</div>}
        <div className={styles.title}>{title}</div>
      </div>

      {riskChip && (
        <div className={styles.riskChip}>
          <Dot color={TONE_COLOR[riskChip.tone]} glow />
          <span className={styles.riskChipLabel} style={{ color: TONE_COLOR[riskChip.tone] }}>
            {riskChip.label}
          </span>
          {riskChip.detail && <span className={styles.riskChipDetail}>{riskChip.detail}</span>}
        </div>
      )}

      {autoState && (
        <div className={styles.autoBadge} data-state={autoState}>
          <Dot color={autoState === 'active' ? 'var(--ap-mint)' : 'var(--ap-rose)'} glow />
          {autoState === 'active' ? 'AUTO' : 'PAUSED'}
        </div>
      )}

      <div className={`${styles.iconBtn} ${styles.bell}`} aria-label="通知" title={`${unresolvedCount} 条未解除风控事件`}>
        <Icon name="bell" size={15} />
        {unresolvedCount > 0 && <span className={styles.bellDot} />}
      </div>
    </header>
  )
}
