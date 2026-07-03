/**
 * Pilot AI 对话抽屉（handoff/02 P10）—— Ctrl/⌘+J 或顶栏按钮唤起。
 * mock 模式：本地脚本化流式回复 + 工具调用轨迹；真后端为 SSE /api/agent/chat。
 */
import { useEffect, useRef, useState } from "react";
import { BrainCircuit, Check, Loader2, Send, X } from "lucide-react";
import type { ChatMessage } from "@/api/types";
import { Pill } from "@/components/ui/atoms";

const QUICK = [
  "当前持仓风险敞口多大？",
  "解释最近一次决策",
  "今天为什么没有开仓？",
  "帮我收紧日亏损阈值",
];

const SCRIPTED: Record<string, { tools: string[]; answer: string; pending?: string }> = {
  默认: {
    tools: ["查询持仓", "查询风控状态"],
    answer:
      "当前持有 BTCUSDT、ETHUSDT 两个多头仓位，合计占权益 12%。日内亏损 -0.48%，距 -3% 熔断线空间充足，风险敞口处于低位。",
  },
  收紧: {
    tools: ["读取当前风控配置"],
    answer:
      "建议将 MAX_DAILY_LOSS_PCT 由 3% 收紧至 2%。该修改属于硬风控变更，需要你人工确认后才会生效。",
    pending: "MAX_DAILY_LOSS_PCT: 3% → 2%",
  },
};

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
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight });
  }, [messages]);

  const send = (text: string) => {
    if (!text.trim() || busy) return;
    const userMsg: ChatMessage = {
      id: `m_${messages.length}_u`,
      role: "user",
      text,
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);

    const script = text.includes("收紧") ? SCRIPTED.收紧 : SCRIPTED.默认;
    const aiId = `m_${messages.length}_a`;

    // 工具轨迹逐条出现 → 正文逐字流式
    setMessages((m) => [
      ...m,
      { id: aiId, role: "assistant", text: "", tools: [] },
    ]);
    script.tools.forEach((t, i) => {
      setTimeout(() => {
        setMessages((m) =>
          m.map((msg) =>
            msg.id === aiId
              ? {
                  ...msg,
                  tools: [
                    ...script.tools.slice(0, i).map((n) => ({ name: n, status: "done" as const })),
                    { name: t, status: "running" as const },
                  ],
                }
              : msg,
          ),
        );
      }, 350 * (i + 1));
    });
    const startText = 350 * (script.tools.length + 1);
    const chars = [...script.answer];
    chars.forEach((_, i) => {
      setTimeout(() => {
        setMessages((m) =>
          m.map((msg) =>
            msg.id === aiId
              ? {
                  ...msg,
                  tools: script.tools.map((n) => ({ name: n, status: "done" as const })),
                  text: script.answer.slice(0, i + 1),
                }
              : msg,
          ),
        );
        if (i === chars.length - 1) {
          setBusy(false);
          if (script.pending) {
            setMessages((m) =>
              m.map((msg) =>
                msg.id === aiId
                  ? {
                      ...msg,
                      pendingAction: { id: "pa_1", label: script.pending! },
                    }
                  : msg,
              ),
            );
          }
        }
      }, startText + i * 14);
    });
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-bg-0/40" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
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
              <div key={m.id} className="ml-10 self-end rounded-md rounded-br-xs bg-bg-3 px-3 py-2 text-sm text-fg-1">
                {m.text}
              </div>
            ) : (
              <div key={m.id} className="mr-6 flex flex-col gap-1.5">
                {m.tools && m.tools.length > 0 && (
                  <div className="flex flex-col gap-1">
                    {m.tools.map((t) => (
                      <div key={t.name} className="flex items-center gap-1.5 font-mono text-micro text-fg-3">
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
                  <div className="flex items-center justify-between rounded-sm border border-amber/30 bg-amber-soft px-3 py-2">
                    <span className="font-mono text-xs text-amber">
                      {m.pendingAction.label}
                    </span>
                    <button className="cursor-pointer rounded-xs bg-amber px-2 py-1 text-micro font-semibold text-bg-0 hover:brightness-110">
                      应用修改（需确认）
                    </button>
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
