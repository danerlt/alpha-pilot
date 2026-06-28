'use client'

import { useEffect, useState } from 'react'
import { Icon } from './Icon'
import styles from './ui.module.css'

export interface ModalProps {
  open: boolean
  title?: string
  onClose?: () => void
  footer?: React.ReactNode
  children?: React.ReactNode
}

export function Modal({ open, title, onClose, footer, children }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose?.()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className={styles.overlay} role="dialog" aria-modal="true" onClick={() => onClose?.()}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {title && <div className={styles.modalHeader}>{title}</div>}
        <div className={styles.modalBody}>{children}</div>
        {footer && <div className={styles.modalFooter}>{footer}</div>}
      </div>
    </div>
  )
}

export interface ConfirmDialogProps {
  open: boolean
  title: string
  message: React.ReactNode
  tone?: 'default' | 'danger'
  confirmLabel?: string
  cancelLabel?: string
  /** 若提供，必须输入完全一致的口令才能确认（如 mainnet 一键平仓的 "CLOSE ALL"）。 */
  requireText?: string
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/**
 * 统一危险操作确认弹窗 — 替换原生 confirm/prompt。
 * 支持 requireText 口令校验，承载 close-all / mainnet 切换等高危流程。
 */
export function ConfirmDialog({
  open,
  title,
  message,
  tone = 'default',
  confirmLabel = '确认',
  cancelLabel = '取消',
  requireText,
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const [typed, setTyped] = useState('')

  useEffect(() => {
    if (!open) setTyped('')
  }, [open])

  const blocked = !!requireText && typed.trim() !== requireText
  const confirmVariant = tone === 'danger' ? styles.button + ' ' + styles.danger : styles.button

  return (
    <Modal
      open={open}
      title={title}
      onClose={busy ? undefined : onCancel}
      footer={
        <>
          <button className={styles.button} data-variant="ghost" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </button>
          <button
            className={confirmVariant}
            data-variant={tone === 'danger' ? 'danger' : 'primary'}
            onClick={onConfirm}
            disabled={busy || blocked}
          >
            {busy ? '处理中…' : confirmLabel}
          </button>
        </>
      }
    >
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        {tone === 'danger' && <Icon name="alert" size={18} color="var(--ap-rose)" />}
        <div style={{ flex: 1 }}>{message}</div>
      </div>
      {requireText && (
        <input
          className={styles.modalField}
          placeholder={`请输入 ${requireText} 以确认`}
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          autoFocus
        />
      )}
    </Modal>
  )
}
