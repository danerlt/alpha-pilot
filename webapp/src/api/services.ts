/**
 * API service 层 —— 页面只 import 这里，唯一一条真实 fetch 路径。
 * 无后端时由 MSW 在网络层拦截（见 mocks/handlers.ts），业务代码不感知。
 * 路径契约见 handoff/03 与 docs/webapp前端架构.md §3。
 */
import { http } from "./client";
import type {
  AccountOverview,
  AccountSnapshot,
  AttributionDim,
  AttributionRow,
  AuditLog,
  DailyReport,
  Decision,
  EventItem,
  HardLimit,
  Kline,
  LabCandidate,
  LabHistoryItem,
  MarketSymbol,
  MonthlyPnl,
  Order,
  OrderBook,
  OrderTicketPayload,
  PerformanceSummary,
  PermissionRow,
  Position,
  PrecheckResult,
  RecentTrade,
  RiskState,
  StrategyCard,
  SymbolConfig,
  Ticker,
  Trade,
  User,
} from "./types";

export const riskApi = {
  state: () => http<RiskState>("/api/risk/state"),
};

export const accountApi = {
  overview: () => http<AccountOverview>("/api/account"),
  history: () => http<AccountSnapshot[]>("/api/account/history"),
};

export const positionsApi = {
  list: () => http<Position[]>("/api/positions"),
  close: (id: string) =>
    http<{ ok: boolean }>(`/api/commands/close-position/${id}`, {
      method: "POST",
    }),
  updateSltp: (id: string, sl: number, tp: number) =>
    http<{ ok: boolean }>(`/api/positions/${id}/sltp`, {
      method: "PATCH",
      body: JSON.stringify({ sl, tp }),
    }),
};

export const ordersApi = {
  list: () => http<Order[]>("/api/orders"),
  precheck: (payload: OrderTicketPayload) =>
    http<PrecheckResult>("/api/orders/precheck", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  place: (payload: OrderTicketPayload) =>
    http<{ ok: boolean }>("/api/orders", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export const tradesApi = {
  list: () => http<Trade[]>("/api/trades"),
};

export const decisionsApi = {
  list: () => http<Decision[]>("/api/decisions"),
  detail: (id: string) => http<Decision | null>(`/api/decisions/${id}`),
};

export const eventsApi = {
  recent: () => http<EventItem[]>("/api/events/catchup"),
};

export const marketApi = {
  symbols: () => http<MarketSymbol[]>("/api/market/symbols"),
  klines: (symbol: string, interval: string, limit = 180) =>
    http<Kline[]>(
      `/api/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`,
    ),
  ticker: (symbol: string) => http<Ticker>(`/api/market/ticker?symbol=${symbol}`),
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
  users: () => http<User[]>("/api/admin/users"),
  permissions: () => http<PermissionRow[]>("/api/admin/roles"),
  approveUser: (id: string) =>
    http<{ ok: boolean }>(`/api/admin/users/${id}/approve`, { method: "POST" }),
};

export const authApi = {
  login: (email: string, password: string) =>
    http<User>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => http<User>("/api/auth/me"),
  logout: () => http<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
};

export const commandsApi = {
  closeAll: () =>
    http<{ taskId: string }>("/api/commands/close-all", { method: "POST" }),
  pause: () => http<{ ok: boolean }>("/api/commands/pause", { method: "POST" }),
  resume: () =>
    http<{ ok: boolean }>("/api/commands/resume", { method: "POST" }),
};
