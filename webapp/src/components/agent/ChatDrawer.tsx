/**
 * Pilot AI 对话抽屉（handoff/02 P10，后端 P3 接真）—— Ctrl/⌘+J 或顶栏按钮唤起。
 * SSE 流式（tool_call→delta→done）+ 会话历史 + pending action 人工确认（admin）。
 */
import { useEffect, useRef, useState } from "react";
import { BrainCircuit, Check, Loader2, Send, X } from "lucide-react";
import type { ChatMessage } from "@/api/types";
import { agentApi } from "@/api/services";
import { streamAgentChat } from "@/api/agentStream";
import { stream } from "@/api/stream";
import { Pill } from "@/components/ui/atoms";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";

const QUICK = [
  "当前持仓风险敞口多大？",
  "解释最近一次决策",
  "今天为什么没有开仓？",
  "帮我收紧日亏损阈值",
];

export function ChatDrawer({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [confirming, setConfirming] = useState<{ msgId: string; actionId: string } | null>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);
  const seqRef = useRef(0);

  // 首次打开加载会话历史
  useEffect(() => {
    if (!open || historyLoaded) return;
    setHistoryLoaded(true);
    agentApi
      .history()
      .then((items) => {
        const restored: ChatMessage[] = [];
        // 后端按时间倒序，恢复为正序对话
        [...items].reverse().forEach((it) => {
          restored.push({ id: `h_${it.invocation_id}_u`, role: "user", text: it.message });
          restored.push({
            id: `h_${it.invocation_id}_a`,
            role: "assistant",
            text: it.answer,
            tools: (it.tools ?? []).map((name) => ({ name, status: "done" as const })),
            pendingAction:
              it.pending_action_id != null
                ? { id: String(it.pending_action_id), label: "待确认的配置修改" }
                : undefined,
          });
        });
        // 历史异步回填不得覆盖已在进行的对话
        setMessages((m) => (m.length > 0 ? m : restored));
      })
      .catch(() => {});
  }, [open, historyLoaded]);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight });
  }, [messages]);

  useEffect(() => () => abortRef.current?.(), []);

  const send = (text: string) => {
    if (!text.trim() || busy) return;
    const n = ++seqRef.current;
    const aiId = `m_${n}_a`;
    setMessages((m) => [
      ...m,
      { id: `m_${n}_u`, role: "user", text },
      { id: aiId, role: "assistant", text: "", tools: [] },
    ]);
    setInput("");
    setBusy(true);

    const patch = (fn: (msg: ChatMessage) => ChatMessage) =>
      setMessages((m) => m.map((msg) => (msg.id === aiId ? fn(msg) : msg)));

    abortRef.current = streamAgentChat(text, {
      onToolCall: (name, status) =>
        patch((msg) => {
          const st = status === "done" ? ("done" as const) : ("running" as const);
          const tools = [...(msg.tools ?? [])];
          const i = tools.findIndex((t) => t.name === name);
          if (i >= 0) tools[i] = { name, status: st };
          else tools.push({ name, status: st });
          return { ...msg, tools };
        }),
      onDelta: (text_) => patch((msg) => ({ ...msg, text: msg.text + text_ })),
      onDone: (_invocationId, pendingActionId) => {
        setBusy(false);
        if (pendingActionId) {
          patch((msg) => ({
            ...msg,
            pendingAction: { id: pendingActionId, label: "待确认的配置修改" },
          }));
        }
      },
      onError: (err) => {
        setBusy(false);
        patch((msg) => ({
          ...msg,
          text: msg.text || `⚠ ${err}`,
        }));
      },
    });
  };

  // 人工确认：admin 白名单复核 + 应用 + 审计（Agent 无权直改硬风控）
  const applyPending = async () => {
    if (!confirming) return;
    try {
      const r = await agentApi.confirmAction(confirming.actionId);
      setMessages((m) =>
        m.map((msg) =>
          msg.id === confirming.msgId && msg.pendingAction
            ? {
                ...msg,
                pendingAction: {
                  ...msg.pendingAction,
                  label: r.key ? `${r.key} → ${r.value}` : msg.pendingAction.label,
                  applied: true,
                },
              }
            : msg,
        ),
      );
      stream.emitEvent({
        kind: "system",
        msg: `Agent 配置修改已人工确认 · ${r.key ?? confirming.actionId} · 已落审计`,
        tone: "amber",
      });
    } catch (e) {
      stream.emitEvent({
        kind: "system",
        msg: `Agent 配置确认失败 · ${e instanceof Error ? e.message : "未知错误"}`,
        tone: "rose",
      });
    } finally {
      setConfirming(null);
    }
  };

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-bg-0/40"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="flex h-full w-[400px] flex-col border-l border-line bg-bg-1 shadow-3">
        {/* header */}
        <div className="flex items-center gap-2.5 border-b border-line-soft px-4 py-3.5">
          <BrainCircuit size={16} className="text-violet" />
          <div className="flex-1">
            <div className="text-sm font-semibold text-fg-1">Pilot AI</div>
            <div className="font-mono text-micro text-fg-4">
              只读工具 · 写操作需人工确认
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-xs border border-line-soft text-fg-4 hover:text-fg-1"
          >
            <X size={14} />
          </button>
        </div>

        {/* messages */}
        <div ref={bodyRef} className="flex flex-1 flex-col gap-3 overflow-auto px-4 py-4">
          {messages.length === 0 && (
            <div className="mt-6 flex flex-col items-center gap-3 text-center">
              <BrainCircuit size={28} className="text-violet" />
              <div className="text-sm text-fg-3">
                问我任何关于持仓、决策、风控的问题
              </div>
            </div>
          )}
          {messages.map((m) =>
            m.role === "user" ? (
              <div
                key={m.id}
                className="ml-10 self-end rounded-md rounded-br-xs bg-bg-3 px-3 py-2 text-sm text-fg-1"
              >
                {m.text}
              </div>
            ) : (
              <div key={m.id} className="mr-6 flex flex-col gap-1.5">
                {m.tools && m.tools.length > 0 && (
                  <div className="flex flex-col gap-1">
                    {m.tools.map((t) => (
                      <div
                        key={t.name}
                        className="flex items-center gap-1.5 font-mono text-micro text-fg-3"
                      >
                        {t.status === "done" ? (
                          <Check size={10} className="text-mint" />
                        ) : (
                          <Loader2 size={10} className="animate-spin text-violet" />
                        )}
                        {t.name}
                      </div>
                    ))}
                  </div>
                )}
                {(m.text || busy) && (
                  <div className="rounded-md rounded-bl-xs border border-violet/20 bg-bg-2 px-3 py-2 text-sm leading-relaxed text-fg-1">
                    {m.text}
                    {busy && m.text.length === 0 && (
                      <span className="font-mono text-fg-4">…</span>
                    )}
                  </div>
                )}
                {m.pendingAction && (
                  <div
                    className={`flex items-center justify-between rounded-sm border px-3 py-2 ${
                      m.pendingAction.applied
                        ? "border-mint/30 bg-mint-soft"
                        : "border-amber/30 bg-amber-soft"
                    }`}
                  >
                    <span
                      className={`font-mono text-xs ${m.pendingAction.applied ? "text-mint" : "text-amber"}`}
                    >
                      {m.pendingAction.label}
                    </span>
                    {m.pendingAction.applied ? (
                      <span className="flex items-center gap-1 font-mono text-micro font-semibold text-mint">
                        <Check size={11} strokeWidth={2.6} /> 已确认生效
                      </span>
                    ) : (
                      <button
                        onClick={() =>
                          setConfirming({ msgId: m.id, actionId: m.pendingAction!.id })
                        }
                        className="cursor-pointer rounded-xs bg-amber px-2 py-1 text-micro font-semibold text-bg-0 hover:brightness-110"
                      >
                        应用修改（需确认）
                      </button>
                    )}
                  </div>
                )}
              </div>
            ),
          )}
        </div>

        {/* quick chips */}
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-1.5 px-4 pb-2">
            {QUICK.map((qq) => (
              <button key={qq} onClick={() => send(qq)} className="cursor-pointer">
                <Pill tone="violet">{qq}</Pill>
              </button>
            ))}
          </div>
        )}

        {/* 人工确认弹窗：Agent 无权绕过直改硬风控 */}
        <ConfirmDialog
          open={confirming !== null}
          onClose={() => setConfirming(null)}
          onConfirm={applyPending}
          title="确认应用 AI 建议的配置修改"
          confirmLabel="确认应用"
          body={
            <>
              将执行 Agent 提议的配置变更（服务端白名单复核）。硬风控修改需人工确认后才生效，
              操作将记录审计日志。
            </>
          }
        />

        {/* input */}
        <div className="flex items-center gap-2 border-t border-line-soft px-4 py-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="输入问题…"
            className="flex-1 rounded-sm border border-line bg-bg-3 px-3 py-2 text-sm text-fg-1 outline-none placeholder:text-fg-4 focus:border-violet"
          />
          <button
            onClick={() => send(input)}
            disabled={busy || !input.trim()}
            className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-sm bg-violet-soft text-violet disabled:opacity-40"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
