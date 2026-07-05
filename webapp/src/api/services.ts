/**
 * API service 层 —— 页面只 import 这里，唯一一条真实 fetch 路径。
 * 无后端时由 MSW 在网络层拦截（见 mocks/handlers.ts），业务代码不感知。
 * 路径契约见 handoff/03 与 docs/webapp前端架构.md §3。
 */
import { http } from "./client";
import {
  fromWireAccount,
  fromWireDecision,
  fromWireDecisionDetail,
  fromWireKline,
  fromWireMarketSymbol,
  fromWirePosition,
  fromWirePrecheck,
  fromWireRiskState,
  fromWireRoles,
  fromWireTicker,
  fromWireTrade,
  fromWireUser,
  type WireAccount,
  type WireDecision,
  type WireDecisionDetail,
  type WireKline,
  type WireLogin,
  type WireMarketSymbol,
  type WirePosition,
  type WirePrecheck,
  type WireRiskState,
  type WireRoles,
  type WireTicker,
  type WireTrade,
  type WireUser,
} from "./wire";
import type {
  AccountSnapshot,
  AttributionDim,
  AttributionRow,
  AuditLog,
  DailyReport,
  EventItem,
  HardLimit,
  LabCandidate,
  LabHistoryItem,
  MonthlyPnl,
  Order,
  OrderBook,
  OrderTicketPayload,
  PerformanceSummary,
  RecentTrade,
  StrategyCard,
  SymbolConfig,
} from "./types";

/** 手动下单 payload → 后端 ManualOrderCreate（snake_case wire 形状） */
function toWireOrder(payload: OrderTicketPayload) {
  return {
    symbol: payload.symbol,
    side: payload.side,
    type: payload.type,
    qty: payload.qty,
    price: payload.price ?? null,
    sl: payload.sl ?? null,
    tp: payload.tp ?? null,
    reduce_only: payload.reduceOnly,
  };
}

export const riskApi = {
  state: () =>
    http<WireRiskState>("/api/risk/state").then(fromWireRiskState),
};

export const accountApi = {
  overview: () => http<WireAccount>("/api/account").then(fromWireAccount),
  // 后端暂缺权益序列端点（见 docs/webapp联调-后端待办.md），真实模式下曲线由
  // account.snapshot 事件增量生长
  history: () => http<AccountSnapshot[]>("/api/account/history"),
};

export const positionsApi = {
  list: () =>
    http<WirePosition[]>("/api/positions").then((ws) => ws.map(fromWirePosition)),
  close: (id: string) =>
    http<{ ok: boolean }>(`/api/commands/close-position/${id}`, {
      method: "POST",
    }),
  updateSltp: (id: string, sl: number, tp: number) =>
    http<{ ok: boolean }>(`/api/positions/${id}/sltp`, {
      method: "PATCH",
      body: JSON.stringify({ stop_loss: sl, take_profit: tp }),
    }),
};

export const ordersApi = {
  // 后端暂缺订单列表端点（见联调待办），真实模式下该调用会 404 → 页面容错为空
  list: () => http<Order[]>("/api/orders/list"),
  precheck: (payload: OrderTicketPayload) =>
    http<WirePrecheck>("/api/orders/precheck", {
      method: "POST",
      body: JSON.stringify(toWireOrder(payload)),
    }).then(fromWirePrecheck),
  place: (payload: OrderTicketPayload) =>
    http<{ order_id?: number }>("/api/orders", {
      method: "POST",
      body: JSON.stringify(toWireOrder(payload)),
    }).then(() => ({ ok: true })),
};

export const tradesApi = {
  list: () => http<WireTrade[]>("/api/trades").then((ws) => ws.map(fromWireTrade)),
};

export const decisionsApi = {
  list: () =>
    http<WireDecision[]>("/api/decisions").then((ws) => ws.map(fromWireDecision)),
  detail: (id: string) =>
    http<WireDecisionDetail | null>(`/api/decisions/${id}`).then((w) =>
      w ? fromWireDecisionDetail(w) : null,
    ),
};

export const eventsApi = {
  // catchup 无 response_model（后端待补）：兼容 EventItem 直出与 EventEnvelope 两种形状
  recent: () =>
    http<unknown[]>("/api/events/catchup").then((rows) =>
      rows.map((r) => toEventItem(r)),
    ),
};

function toEventItem(r: unknown): EventItem {
  const o = r as Record<string, unknown>;
  if (typeof o.msg === "string") return o as unknown as EventItem; // mock 直出形状
  const eventType = String(o.event_type ?? "event");
  return {
    id: String(o.event_id ?? o.id ?? Math.random()),
    ts: String(o.occurred_at ?? "").slice(11, 19),
    kind: eventType.startsWith("decision.")
      ? "ai"
      : eventType.startsWith("order.") || eventType.startsWith("trade.")
        ? "fill"
        : eventType.startsWith("risk.") || eventType.startsWith("circuit")
          ? "breaker"
          : "system",
    msg: eventType,
    tone: eventType.startsWith("decision.")
      ? "violet"
      : eventType.startsWith("risk.") || eventType.startsWith("circuit")
        ? "rose"
        : "fg",
  };
}

export const marketApi = {
  symbols: () =>
    http<WireMarketSymbol[]>("/api/market/symbols").then((ws) =>
      ws.map(fromWireMarketSymbol),
    ),
  klines: (symbol: string, interval: string, limit = 180) =>
    http<WireKline[]>(
      `/api/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`,
    ).then((ws) => ws.map(fromWireKline)),
  ticker: (symbol: string) =>
    http<WireTicker>(`/api/market/ticker?symbol=${symbol}`).then(fromWireTicker),
  // 盘口/逐笔为 P2b WS 代理范围（后端进行中），暂 mock-only
  orderBook: (symbol: string) =>
    http<OrderBook>(`/api/market/depth?symbol=${symbol}`),
  recentTrades: (symbol: string) =>
    http<RecentTrade[]>(`/api/market/trades?symbol=${symbol}`),
};

export const performanceApi = {
  summary: () => http<PerformanceSummary>("/api/performance/summary"),
  monthly: () => http<MonthlyPnl[]>("/api/performance/monthly"),
  attribution: (dim: AttributionDim) =>
    http<AttributionRow[]>(`/api/performance/attribution?dim=${dim}`),
};

export const strategyApi = {
  list: () => http<StrategyCard[]>("/api/strategies"),
  toggle: (id: string, enabled: boolean) =>
    http<{ ok: boolean }>(`/api/strategies/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }),
  hardLimits: () => http<HardLimit[]>("/api/config/runtime"),
  symbolConfigs: () => http<SymbolConfig[]>("/api/admin/symbols"),
};

export const labApi = {
  candidates: () => http<LabCandidate[]>("/api/lab/candidates"),
  history: () => http<LabHistoryItem[]>("/api/lab/history"),
  start: (id: string) =>
    http<{ ok: boolean }>(`/api/lab/candidates/${id}/start`, { method: "POST" }),
  promote: (id: string) =>
    http<{ ok: boolean }>(`/api/lab/candidates/${id}/promote`, {
      method: "POST",
    }),
  terminate: (id: string) =>
    http<{ ok: boolean }>(`/api/lab/candidates/${id}/terminate`, {
      method: "POST",
    }),
};

export const auditApi = {
  logs: () => http<AuditLog[]>("/api/admin/audit-logs"),
  reports: () => http<DailyReport[]>("/api/reports"),
};

export const adminApi = {
  users: () =>
    http<WireUser[]>("/api/admin/users").then((ws) => ws.map(fromWireUser)),
  permissions: () =>
    http<WireRoles>("/api/admin/roles").then(fromWireRoles),
  approveUser: (id: string) =>
    http<{ ok: boolean }>(`/api/admin/users/${id}/approve`, { method: "POST" }),
};

export const authApi = {
  login: (email: string, password: string) =>
    http<WireLogin>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }).then((w) => fromWireUser(w.user)),
  me: () => http<WireUser>("/api/auth/me").then(fromWireUser),
  logout: () => http<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
};

export const commandsApi = {
  closeAll: () =>
    http<{ taskId: string }>("/api/commands/close-all", { method: "POST" }),
  pause: () => http<{ ok: boolean }>("/api/commands/pause", { method: "POST" }),
  resume: () =>
    http<{ ok: boolean }>("/api/commands/resume", { method: "POST" }),
};
