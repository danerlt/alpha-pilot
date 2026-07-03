/**
 * API service 层 —— 页面只 import 这里，不感知 mock/真实后端。
 * 真实路径按 handoff/03 契约与仓库现有 REST API 对齐。
 */
import { USE_MOCK, delay, http } from "./client";
import * as mock from "./mock/data";
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
  state(): Promise<RiskState> {
    if (USE_MOCK) return delay({ ...mock.mockRiskState });
    return http("/api/risk/state");
  },
};

export const accountApi = {
  overview(): Promise<AccountOverview> {
    if (USE_MOCK) return delay({ ...mock.mockAccount });
    return http("/api/account");
  },
  history(): Promise<AccountSnapshot[]> {
    if (USE_MOCK) return delay([...mock.mockEquitySeries]);
    return http("/api/account/history");
  },
};

export const positionsApi = {
  list(): Promise<Position[]> {
    if (USE_MOCK) return delay(mock.mockPositions.map((p) => ({ ...p })));
    return http("/api/positions");
  },
  close(id: string): Promise<{ ok: boolean }> {
    if (USE_MOCK) {
      const i = mock.mockPositions.findIndex((p) => p.id === id);
      if (i >= 0) mock.mockPositions.splice(i, 1);
      return delay({ ok: true }, 400);
    }
    return http(`/api/commands/close-position/${id}`, { method: "POST" });
  },
  updateSltp(id: string, sl: number, tp: number): Promise<{ ok: boolean }> {
    if (USE_MOCK) {
      const p = mock.mockPositions.find((x) => x.id === id);
      if (p) {
        p.sl = sl;
        p.tp = tp;
      }
      return delay({ ok: true }, 300);
    }
    return http(`/api/positions/${id}/sltp`, {
      method: "PATCH",
      body: JSON.stringify({ sl, tp }),
    });
  },
};

export const ordersApi = {
  list(): Promise<Order[]> {
    if (USE_MOCK) return delay(mock.mockOrders.map((o) => ({ ...o })));
    return http("/api/orders");
  },
  precheck(payload: OrderTicketPayload): Promise<PrecheckResult> {
    if (USE_MOCK) {
      const qtyOk = payload.qty > 0;
      const riskOk = payload.sl !== undefined || payload.reduceOnly;
      const sizeOk = payload.qty * (payload.price ?? 68863) < 25000;
      const items = [
        { check: "qty_valid", pass: qtyOk, note: qtyOk ? "数量合法" : "数量必须大于 0" },
        { check: "stop_loss_set", pass: riskOk, note: riskOk ? "止损已设置" : "开仓必须设置止损" },
        { check: "max_position_size", pass: sizeOk, note: sizeOk ? "< 20% 权益" : "超出单仓位上限 20%" },
        { check: "daily_loss_limit", pass: true, note: "-0.48% > -3.0%" },
        { check: "halted_check", pass: true, note: "风控状态 OK" },
      ];
      const pass = items.every((i) => i.pass);
      return delay({ verdict: pass ? "PASS" : "REJECT", items }, 350);
    }
    return http("/api/orders/precheck", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  place(payload: OrderTicketPayload): Promise<{ ok: boolean }> {
    if (USE_MOCK) {
      mock.mockOrders.unshift({
        id: `o_m${mock.mockOrders.length + 1}`,
        ts: "刚刚",
        symbol: payload.symbol,
        side: payload.side,
        type: payload.type,
        qty: payload.qty,
        price: payload.price ?? 0,
        status: payload.type === "MARKET" ? "FILLED" : "WORKING",
      });
      return delay({ ok: true }, 500);
    }
    return http("/api/orders", { method: "POST", body: JSON.stringify(payload) });
  },
};

export const tradesApi = {
  list(): Promise<Trade[]> {
    if (USE_MOCK) return delay(mock.mockTrades.map((t) => ({ ...t })));
    return http("/api/trades");
  },
};

export const decisionsApi = {
  list(): Promise<Decision[]> {
    if (USE_MOCK) return delay(mock.mockDecisions.map((d) => ({ ...d })));
    return http("/api/decisions");
  },
  detail(id: string): Promise<Decision | undefined> {
    if (USE_MOCK)
      return delay(mock.mockDecisions.find((d) => d.id === id));
    return http(`/api/decisions/${id}`);
  },
};

export const eventsApi = {
  recent(): Promise<EventItem[]> {
    if (USE_MOCK) return delay(mock.mockEvents.map((e) => ({ ...e })));
    return http("/api/events/catchup");
  },
};

export const marketApi = {
  symbols(): Promise<MarketSymbol[]> {
    if (USE_MOCK) return delay(mock.mockSymbols.map((s) => ({ ...s })));
    return http("/api/market/symbols");
  },
  klines(symbol: string, interval: string, limit = 180): Promise<Kline[]> {
    if (USE_MOCK) return delay(mock.genKlines(symbol, limit), 220);
    return http(
      `/api/market/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`,
    );
  },
  ticker(symbol: string): Promise<Ticker> {
    if (USE_MOCK) return delay(mock.genTicker(symbol));
    return http(`/api/market/ticker?symbol=${symbol}`);
  },
  orderBook(symbol: string): Promise<OrderBook> {
    if (USE_MOCK) return delay(mock.genOrderBook(symbol), 120);
    return http(`/api/market/depth?symbol=${symbol}`);
  },
  recentTrades(symbol: string): Promise<RecentTrade[]> {
    if (USE_MOCK) return delay(mock.genRecentTrades(symbol), 120);
    return http(`/api/market/trades?symbol=${symbol}`);
  },
};

export const performanceApi = {
  summary(): Promise<PerformanceSummary> {
    if (USE_MOCK) return delay({ ...mock.mockPerformance });
    return http("/api/performance/summary");
  },
  monthly(): Promise<MonthlyPnl[]> {
    if (USE_MOCK) return delay([...mock.mockMonthlyPnl]);
    return http("/api/performance/monthly");
  },
  attribution(dim: AttributionDim): Promise<AttributionRow[]> {
    if (USE_MOCK) return delay([...(mock.mockAttribution[dim] ?? [])]);
    return http(`/api/performance/attribution?dim=${dim}`);
  },
};

export const strategyApi = {
  list(): Promise<StrategyCard[]> {
    if (USE_MOCK) return delay(mock.mockStrategies.map((s) => ({ ...s })));
    return http("/api/strategies");
  },
  toggle(id: string, enabled: boolean): Promise<{ ok: boolean }> {
    if (USE_MOCK) {
      const s = mock.mockStrategies.find((x) => x.id === id);
      if (s) s.enabled = enabled;
      return delay({ ok: true }, 250);
    }
    return http(`/api/strategies/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    });
  },
  hardLimits(): Promise<HardLimit[]> {
    if (USE_MOCK) return delay([...mock.mockHardLimits]);
    return http("/api/config/runtime");
  },
  symbolConfigs(): Promise<SymbolConfig[]> {
    if (USE_MOCK) return delay(mock.mockSymbolConfigs.map((s) => ({ ...s })));
    return http("/api/admin/symbols");
  },
};

export const labApi = {
  candidates(): Promise<LabCandidate[]> {
    if (USE_MOCK) return delay(mock.mockLabCandidates.map((c) => ({ ...c })));
    return http("/api/lab/candidates");
  },
  history(): Promise<LabHistoryItem[]> {
    if (USE_MOCK) return delay([...mock.mockLabHistory]);
    return http("/api/lab/history");
  },
};

export const auditApi = {
  logs(): Promise<AuditLog[]> {
    if (USE_MOCK) return delay(mock.mockAuditLogs.map((a) => ({ ...a })));
    return http("/api/admin/audit-logs");
  },
  reports(): Promise<DailyReport[]> {
    if (USE_MOCK) return delay(mock.mockReports.map((r) => ({ ...r })));
    return http("/api/reports");
  },
};

export const adminApi = {
  users(): Promise<User[]> {
    if (USE_MOCK) return delay(mock.mockUsers.map((u) => ({ ...u })));
    return http("/api/admin/users");
  },
  permissions(): Promise<PermissionRow[]> {
    if (USE_MOCK) return delay([...mock.mockPermissions]);
    return http("/api/admin/roles");
  },
  approveUser(id: string): Promise<{ ok: boolean }> {
    if (USE_MOCK) {
      const u = mock.mockUsers.find((x) => x.id === id);
      if (u) u.status = "active";
      return delay({ ok: true }, 300);
    }
    return http(`/api/admin/users/${id}/approve`, { method: "POST" });
  },
};

export const commandsApi = {
  closeAll(): Promise<{ taskId: string }> {
    if (USE_MOCK) {
      mock.mockPositions.splice(0, mock.mockPositions.length);
      return delay({ taskId: "task_mock_1" }, 600);
    }
    return http("/api/commands/close-all", { method: "POST" });
  },
  pause(): Promise<{ ok: boolean }> {
    if (USE_MOCK) return delay({ ok: true }, 300);
    return http("/api/commands/pause", { method: "POST" });
  },
  resume(): Promise<{ ok: boolean }> {
    if (USE_MOCK) return delay({ ok: true }, 300);
    return http("/api/commands/resume", { method: "POST" });
  },
};
