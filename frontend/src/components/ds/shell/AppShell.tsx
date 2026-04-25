'use client'

import * as React from 'react'
import { Sidebar } from './Sidebar'
import { Topbar, TopbarProps } from './Topbar'

export interface AppShellProps {
  children: React.ReactNode
  pageTitle: string
  pageSub?: string
  topbar?: Partial<TopbarProps>
  sidebar?: {
    equity?: number
    equityChangePct?: number
    engineRunning?: boolean
    engineLatencyMs?: number
  }
}

export function AppShell({
  children,
  pageTitle, pageSub,
  topbar = {},
  sidebar = {},
}: AppShellProps) {
  return (
    <div
      style={{
        display: 'flex', width: '100%', height: '100vh',
        background: 'var(--ap-bg-0)',
      }}
    >
      <Sidebar {...sidebar} />
      <div
        style={{
          flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0,
        }}
      >
        <Topbar pageTitle={pageTitle} pageSub={pageSub} {...topbar} />
        <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
          {children}
        </div>
      </div>
    </div>
  )
}
