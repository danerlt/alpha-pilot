'use client'

/**
 * Icon — Lucide 图标 inline SVG 实现，避免 lucide-react 网络依赖。
 * V0.1 只内置 Dashboard 用得到的常用图标; 后续按需添加。
 */
import * as React from 'react'

type IconName =
  | 'dashboard'
  | 'brain'
  | 'layers'
  | 'chart'
  | 'shield'
  | 'list'
  | 'settings'
  | 'search'
  | 'bell'
  | 'play'
  | 'pause'
  | 'check'
  | 'x'
  | 'arrow_up'
  | 'arrow_down'
  | 'alert'
  | 'bolt'
  | 'clock'
  | 'book'
  | 'chevron_right'
  | 'chevron_down'
  | 'circle'

const PATHS: Record<IconName, React.ReactNode> = {
  dashboard: (<>
    <rect x="3" y="3" width="7" height="9" rx="1" />
    <rect x="14" y="3" width="7" height="5" rx="1" />
    <rect x="14" y="12" width="7" height="9" rx="1" />
    <rect x="3" y="16" width="7" height="5" rx="1" />
  </>),
  brain: (<>
    <path d="M12 5a3 3 0 0 0-5.99.14A3 3 0 0 0 4 10.5v0a3 3 0 0 0 .14 4A3 3 0 0 0 6 19.99 3 3 0 0 0 12 19V5Z" />
    <path d="M12 5a3 3 0 0 1 5.99.14A3 3 0 0 1 20 10.5v0a3 3 0 0 1-.14 4A3 3 0 0 1 18 19.99 3 3 0 0 1 12 19V5Z" />
  </>),
  layers: (<>
    <path d="m12 2 8 5-8 5-8-5 8-5Z" />
    <path d="m4 12 8 5 8-5" />
    <path d="m4 17 8 5 8-5" />
  </>),
  chart: (<>
    <path d="M3 3v18h18" />
    <path d="m7 16 4-7 4 3 5-9" />
  </>),
  shield: (<><path d="M12 2 4 6v6c0 5 3.5 9 8 10 4.5-1 8-5 8-10V6l-8-4Z" /></>),
  list: (<>
    <line x1="8" x2="21" y1="6" y2="6" />
    <line x1="8" x2="21" y1="12" y2="12" />
    <line x1="8" x2="21" y1="18" y2="18" />
    <circle cx="4" cy="6" r="1" />
    <circle cx="4" cy="12" r="1" />
    <circle cx="4" cy="18" r="1" />
  </>),
  settings: (<>
    <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
  </>),
  search: (<>
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.3-4.3" />
  </>),
  bell: (<>
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
  </>),
  play: (<polygon points="6 3 20 12 6 21 6 3" />),
  pause: (<>
    <rect x="6" y="4" width="4" height="16" />
    <rect x="14" y="4" width="4" height="16" />
  </>),
  check: (<path d="M20 6 9 17l-5-5" />),
  x: (<>
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </>),
  arrow_up: (<>
    <path d="m5 12 7-7 7 7" />
    <path d="M12 19V5" />
  </>),
  arrow_down: (<>
    <path d="M12 5v14" />
    <path d="m19 12-7 7-7-7" />
  </>),
  alert: (<>
    <path d="M12 9v4" />
    <path d="M12 17h.01" />
    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
  </>),
  bolt: (<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" />),
  clock: (<>
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </>),
  book: (<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />),
  chevron_right: (<path d="m9 18 6-6-6-6" />),
  chevron_down: (<path d="m6 9 6 6 6-6" />),
  circle: (<circle cx="12" cy="12" r="10" />),
}

export interface IconProps {
  name: IconName
  size?: number
  color?: string
  strokeWidth?: number
  className?: string
}

export function Icon({ name, size = 16, color = 'currentColor', strokeWidth = 1.8, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ flexShrink: 0 }}
      className={className}
    >
      {PATHS[name]}
    </svg>
  )
}

export type { IconName }
