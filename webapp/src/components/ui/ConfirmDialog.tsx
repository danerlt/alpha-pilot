/** 危险操作二次确认 —— 支持 requireText 口令校验（如输入 CLOSE ALL） */
import { useState, type ReactNode } from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  body,
  confirmLabel = "确认执行",
  requireText,
  busy = false,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: ReactNode;
  body: ReactNode;
  confirmLabel?: string;
  requireText?: string;
  busy?: boolean;
}) {
  const [text, setText] = useState("");
  const blocked = requireText !== undefined && text !== requireText;
  return (
    <Modal open={open} onClose={onClose} title={title}>
      <div className="flex flex-col gap-4">
        <div className="text-sm leading-relaxed text-fg-2">{body}</div>
        {requireText && (
          <div className="flex flex-col gap-1.5">
            <div className="text-xs text-fg-3">
              输入 <span className="font-mono font-semibold text-rose">{requireText}</span> 以确认：
            </div>
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="rounded-sm border border-line bg-bg-4 px-3 py-2 font-mono text-sm text-fg-1 outline-none focus:border-rose"
              placeholder={requireText}
              autoFocus
            />
          </div>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button
            variant="danger"
            disabled={blocked || busy}
            onClick={() => {
              onConfirm();
              setText("");
            }}
          >
            {busy ? "执行中…" : confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
