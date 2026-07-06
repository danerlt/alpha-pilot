/**
 * API service 层 —— 页面只 import 这里，唯一一条真实 fetch 路径。
 * 无后端时由 MSW 在网络层拦截（见 mocks/handlers.ts），业务代码不感知。
 * 路径契约见 handoff/03 与 docs/webapp前端架构.md §3。
 */
import { http } from "./client";
import { envelopeToEventItem, type BackendEnvelope } from "./stream";
import { setWsToken } from "./tokenStore";
import {
  fromWireAccount,
  fromWireAttribution,
  fromWireMonthly,
  fromWireOrder,
  fromWirePerfSummary,
  fromWireRiskLimits,
  fromWireDecision,
  fromWireDecisionDetail,
  fromWireExchangeSettings,
  fromWireExchangeTest,
  fromWireKline,
  fromWireLabCandidate,
  fromWireLabHistory,
  fromWireLlmSettings,
  fromWireLlmTest,
  fromWireNotificationSettings,
  fromWireMarketSymbol,
  fromWirePosition,
  fromWirePrecheck,
  fromWireRiskState,
  fromWireRoles,
  fromWireTicker,
  fromWireTrade,
  fromWireUser,
  type WireAccount,
  type WireAttribution,
  type WireCatchup,
  type WireDecision,
  type WireDecisionDetail,
  type WireExchangeSettings,
  type WireExchangeTest,
  type WireKline,
  type WireLabCandidate,
  type WireLabHistory,
  type WireLlmSettings,
  type WireLlmTest,
  type WireLogin,
  type WireMarketSymbol,
  type WireMonthlyPnl,
  type WireNotificationSettings,
  type WireOrder,
  type WirePerfSummary,
  type WirePosition,
  type WirePrecheck,
  type WireRiskLimits,
  type WireRiskState,
  type WireRoles,
  type WireTicker,
  type WireTrade,
  type WireUser,
} from "./wire";
import type {
  AccountSnapshot,
  AttributionDim,
  AuditLog,
  DailyReport,
  OrderTicketPayload,
  StrategyCard,
  SymbolConfig,
  User,
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
  list: () =>
    http<WireOrder[]>("/api/orders").then((ws) => ws.map(fromWireOrder)),
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
  recent: () =>
    http<WireCatchup>("/api/events/catchup").then((o) =>
      o.events.map((e) =>
        envelopeToEventItem(e.envelope as unknown as BackendEnvelope),
      ),
    ),
};

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
  // 盘口/逐笔走 /ws/market 行情流，见 marketStream.ts
};

export const performanceApi = {
  summary: () =>
    http<WirePerfSummary>("/api/performance/summary").then(fromWirePerfSummary),
  monthly: () =>
    http<WireMonthlyPnl[]>("/api/performance/monthly").then((ws) =>
      ws.map(fromWireMonthly),
    ),
  attribution: (dim: AttributionDim) =>
    http<WireAttribution[]>(`/api/performance/attribution?dim=${dim}`).then(
      (ws) => ws.map(fromWireAttribution),
    ),
};

export const strategyApi = {
  list: () => http<StrategyCard[]>("/api/strategies"),
  toggle: (id: string, enabled: boolean) =>
    http<{ ok: boolean }>(`/api/strategies/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }),
  hardLimits: () =>
    http<WireRiskLimits>("/api/risk/limits").then(fromWireRiskLimits),
  symbolConfigs: () => http<SymbolConfig[]>("/api/admin/symbols"),
};

export const labApi = {
  candidates: () =>
    http<WireLabCandidate[]>("/api/lab/candidates").then((ws) =>
      ws.map(fromWireLabCandidate),
    ),
  history: () =>
    http<WireLabHistory[]>("/api/lab/history").then((ws) =>
      ws.map(fromWireLabHistory),
    ),
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

export interface LoginResult {
  user: User | null;
  requires2fa: boolean;
  twoFaToken: string | null;
}

export const authApi = {
  login: (email: string, password: string): Promise<LoginResult> =>
    http<WireLogin>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }).then((w) => {
      if (w.user) setWsToken(w.access_token ?? null);
      return {
        user: w.user ? fromWireUser(w.user) : null,
        requires2fa: w.requires_2fa ?? false,
        twoFaToken: w.two_fa_token ?? null,
      };
    }),
  /** 2FA 二段式：login 返回 requires_2fa 后，用动态码 + 票据换正式会话 */
  twoFaLogin: (code: string, twoFaToken: string): Promise<User> =>
    http<WireLogin>("/api/auth/2fa/login", {
      method: "POST",
      body: JSON.stringify({ code, two_fa_token: twoFaToken }),
    }).then((w) => {
      setWsToken(w.access_token ?? null);
      return fromWireUser(w.user!);
    }),
  me: () => http<WireUser>("/api/auth/me").then(fromWireUser),
  logout: () =>
    http<{ ok: boolean }>("/api/auth/logout", { method: "POST" }).finally(
      () => setWsToken(null),
    ),
};

export interface ExchangeSettingsUpdate {
  network?: "testnet" | "mainnet";
  apiKey?: string;
  apiSecret?: string;
}

export interface LlmSettingsUpdate {
  model?: string;
  baseUrl?: string;
  apiKey?: string;
  temperature?: number;
  timeoutSeconds?: number;
  agentModels?: Record<string, string>;
}

export const settingsApi = {
  getExchange: () =>
    http<WireExchangeSettings>("/api/settings/exchange").then(
      fromWireExchangeSettings,
    ),
  updateExchange: (u: ExchangeSettingsUpdate) =>
    http<WireExchangeSettings>("/api/settings/exchange", {
      method: "PUT",
      body: JSON.stringify({
        network: u.network,
        api_key: u.apiKey,
        api_secret: u.apiSecret,
      }),
    }).then(fromWireExchangeSettings),
  testExchange: () =>
    http<WireExchangeTest>("/api/settings/exchange/test", {
      method: "POST",
    }).then(fromWireExchangeTest),
  getLlm: () =>
    http<WireLlmSettings>("/api/settings/llm").then(fromWireLlmSettings),
  updateLlm: (u: LlmSettingsUpdate) =>
    http<WireLlmSettings>("/api/settings/llm", {
      method: "PUT",
      body: JSON.stringify({
        model: u.model,
        base_url: u.baseUrl,
        api_key: u.apiKey,
        temperature: u.temperature,
        timeout_seconds: u.timeoutSeconds,
        agent_models: u.agentModels,
      }),
    }).then(fromWireLlmSettings),
  testLlm: () =>
    http<WireLlmTest>("/api/settings/llm/test", { method: "POST" }).then(
      fromWireLlmTest,
    ),
  getNotifications: () =>
    http<WireNotificationSettings>("/api/settings/notifications").then(
      fromWireNotificationSettings,
    ),
  updateNotifications: (u: {
    channels?: Record<string, boolean>;
    subscriptions?: Record<string, boolean>;
  }) =>
    http<WireNotificationSettings>("/api/settings/notifications", {
      method: "PUT",
      body: JSON.stringify(u),
    }).then(fromWireNotificationSettings),
};

export const commandsApi = {
  closeAll: () =>
    http<{ taskId: string }>("/api/commands/close-all", { method: "POST" }),
  pause: () => http<{ ok: boolean }>("/api/commands/pause", { method: "POST" }),
  resume: () =>
    http<{ ok: boolean }>("/api/commands/resume", { method: "POST" }),
};
