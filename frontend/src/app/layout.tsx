import type { Metadata } from 'next'
import '@/styles/design-system.css'
import './globals.css'
import { AppShell } from '@/components/app-shell'
import { AuthProvider } from '@/components/auth-provider'

export const metadata: Metadata = {
  title: 'AlphaPilot',
  description: 'AI 自主数字货币交易系统',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body>
        <div className="shellAmbient shellAmbientA" aria-hidden="true" />
        <div className="shellAmbient shellAmbientB" aria-hidden="true" />
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  )
}
