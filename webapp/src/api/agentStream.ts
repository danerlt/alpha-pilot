/**
 * Pilot AI 对话流 —— POST /api/agent/chat SSE（handoff 3.4）。
 * 事件序：tool_call {name, status:start|done} → delta {text} → done {invocation_id, pending_action_id?}。
 * POST 型 SSE 用 fetch + ReadableStream 手工解析；mock 模式走本地脚本时间线。
 */
import { USE_MOCK } from "./client";
import { config } from "@/config";

export interface AgentChatCallbacks {
  onToolCall: (name: string, status: "start" | "done") => void;
  onDelta: (text: string) => void;
  onDone: (invocationId: string, pendingActionId: string | null) => void;
  onError: (msg: string) => void;
}

/** 发起一次对话流；返回中断函数 */
export function streamAgentChat(
  message: string,
  cb: AgentChatCallbacks,
): () => void {
  if (USE_MOCK) return mockChat(message, cb);
  return sseChat(message, cb);
}

// ---------- mock：脚本化时间线 ----------
const SCRIPTED: Record<
  string,
  { tools: string[]; answer: string; pendingActionId?: string }
> = {
  默认: {
    tools: ["get_positions", "get_risk_state"],
    answer:
      "当前持有 BTCUSDT、ETHUSDT 两个多头仓位，合计占权益 12%。日内亏损 -0.48%，距 -3% 熔断线空间充足，风险敞口处于低位。",
  },
  收紧: {
    tools: ["get_risk_limits"],
    answer:
      "建议将 MAX_DAILY_LOSS_PCT 由 3% 收紧至 2%。该修改属于硬风控变更，需要你人工确认后才会生效。",
    pendingActionId: "1",
  },
};

function mockChat(message: string, cb: AgentChatCallbacks): () => void {
  const script = message.includes("收紧") ? SCRIPTED.收紧 : SCRIPTED.默认;
  const timers: ReturnType<typeof setTimeout>[] = [];
  script.tools.forEach((t, i) => {
    timers.push(setTimeout(() => cb.onToolCall(t, "start"), 300 + i * 500));
    timers.push(setTimeout(() => cb.onToolCall(t, "done"), 650 + i * 500));
  });
  const start = 400 + script.tools.length * 500;
  const chunks = script.answer.match(/.{1,6}/g) ?? [];
  chunks.forEach((c, i) => {
    timers.push(setTimeout(() => cb.onDelta(c), start + i * 60));
  });
  timers.push(
    setTimeout(
      () => cb.onDone("mock-1", script.pendingActionId ?? null),
      start + chunks.length * 60 + 100,
    ),
  );
  return () => timers.forEach(clearTimeout);
}

// ---------- 真后端：fetch SSE ----------
function sseChat(message: string, cb: AgentChatCallbacks): () => void {
  const controller = new AbortController();

  void (async () => {
    try {
      const res = await fetch(`${config.apiBaseUrl}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        cb.onError(`对话请求失败（${res.status}）`);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        // SSE 帧以空行分隔
        let idx: number;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          const frame = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          const evMatch = frame.match(/^event: (.+)$/m);
          const dataMatch = frame.match(/^data: (.+)$/m);
          if (!evMatch || !dataMatch) continue;
          const data = JSON.parse(dataMatch[1]) as Record<string, unknown>;
          switch (evMatch[1]) {
            case "tool_call":
              cb.onToolCall(
                String(data.name ?? ""),
                data.status === "done" ? "done" : "start",
              );
              break;
            case "delta":
              cb.onDelta(String(data.text ?? ""));
              break;
            case "done":
              cb.onDone(
                String(data.invocation_id ?? ""),
                data.pending_action_id != null
                  ? String(data.pending_action_id)
                  : null,
              );
              break;
          }
        }
      }
    } catch (e) {
      if (!controller.signal.aborted) {
        cb.onError(e instanceof Error ? e.message : "对话流中断");
      }
    }
  })();

  return () => controller.abort();
}
