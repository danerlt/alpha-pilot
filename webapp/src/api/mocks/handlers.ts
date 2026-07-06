/**
 * MSW handlers —— dev（无后端）与测试共用的网络层 mock。
 * 响应形状与后端统一响应包严格一致（{success, code, message, data}），
 * 对应真实端点落地后：删除这里的 handler 即可，业务代码零改动。
 */
import { HttpResponse, delay, http } from "msw";
import * as mock from "../mock/data";
import * as wire from "./wireMocks";

/** 后端 ManualOrderCreate wire 形状（precheck / 下单入参） */
interface WireOrderBody {
  symbol: string;
  side: "BUY" | "SELL";
  type: string;
  qty: number;
  price?: number | null;
  sl?: number | null;
  tp?: number | null;
  reduce_only: boolean;
}

function ok(data: unknown) {
  return HttpResponse.json({
    success: true,
    code: "0",
    message: "ok",
    data,
    request_id: "mock",
  });
}

/** 模拟网络延迟，让 loading 态可见 */
const LATENCY = 160;

/** 设置分区的会话内模块态（形状 = 后端 P4 wire 契约） */
const settingsState = {
  exchange: {
    network: "testnet" as string,
    api_key_masked: "****3f2a" as string | null,
    has_secret: true,
  },
  llm: {
    model: "deepseek-v4-pro",
    base_url: "https://api.deepseek.com/v1",
    api_key_masked: "****a1b2" as string | null,
    temperature: 0.3,
    timeout_seconds: 30,
    agent_models: {
      decision: "deepseek-reasoner",
      signal: "deepseek-chat",
      review: "deepseek-chat",
    } as Record<string, string>,
  },
  notify: {
    channels: { telegram: true, discord: false } as Record<string, boolean>,
    subscriptions: {
      circuit_breaker: true,
      order_filled: true,
      position_closed: true,
      daily_report: false,
    } as Record<string, boolean>,
    telegram_bot_token_masked: "****bot9",
    telegram_chat_id: "-100123456",
    min_severity: "info",
  },
};

export const handlers = [
  // ---------- 风控 / 账户（wire 形状，与真实后端同构） ----------
  http.get("/api/risk/state", async () => {
    await delay(LATENCY);
    return ok(wire.toWireRiskState(mock.mockRiskState));
  }),
  http.get("/api/account", async () => {
    await delay(LATENCY);
    return ok(wire.toWireAccount());
  }),
  http.get("/api/account/history", async () => {
    await delay(LATENCY);
    return ok([...mock.mockEquitySeries]);
  }),

  // ---------- 持仓 / 订单 / 交易 ----------
  http.get("/api/positions", async () => {
    await delay(LATENCY);
    return ok(mock.mockPositions.map(wire.toWirePosition));
  }),
  http.post("/api/commands/close-position/:id", async ({ params }) => {
    await delay(400);
    const i = mock.mockPositions.findIndex(
      (p) => String(Number(p.id.replace(/\D/g, "")) || 1) === params.id,
    );
    if (i >= 0) mock.mockPositions.splice(i, 1);
    return ok({ ok: true });
  }),
  http.patch("/api/positions/:id/sltp", async ({ params, request }) => {
    await delay(300);
    const body = (await request.json()) as { stop_loss: number; take_profit: number };
    const p = mock.mockPositions.find(
      (x) => String(Number(x.id.replace(/\D/g, "")) || 1) === params.id,
    );
    if (p) {
      p.sl = body.stop_loss;
      p.tp = body.take_profit;
    }
    return ok({ position_id: params.id, stop_loss: body.stop_loss, take_profit: body.take_profit });
  }),
  http.get("/api/orders", async () => {
    await delay(LATENCY);
    return ok(mock.mockOrders.map(wire.toWireOrder));
  }),
  http.post("/api/orders/precheck", async ({ request }) => {
    await delay(350);
    const payload = (await request.json()) as WireOrderBody;
    const qtyOk = payload.qty > 0;
    const riskOk = payload.sl != null || payload.reduce_only;
    const sizeOk = payload.qty * (payload.price ?? 68863) < 25000;
    const checks = [
      { check: "qty_valid", pass: qtyOk, note: qtyOk ? "数量合法" : "数量必须大于 0" },
      { check: "stop_loss_set", pass: riskOk, note: riskOk ? "止损已设置" : "开仓必须设置止损" },
      { check: "max_position_size", pass: sizeOk, note: sizeOk ? "< 20% 权益" : "超出单仓位上限 20%" },
      { check: "daily_loss_limit", pass: true, note: "-0.48% > -3.0%" },
      { check: "halted_check", pass: true, note: "风控状态 OK" },
    ];
    const pass = checks.every((i) => i.pass);
    return ok({
      verdict: pass ? "PASS" : "REJECT",
      halted: false,
      checks,
      context: {},
    });
  }),
  http.post("/api/orders", async ({ request }) => {
    await delay(500);
    const payload = (await request.json()) as WireOrderBody;
    mock.mockOrders.unshift({
      id: `o_m${mock.mockOrders.length + 1}`,
      ts: "刚刚",
      symbol: payload.symbol,
      side: payload.side,
      type: payload.type as (typeof mock.mockOrders)[0]["type"],
      qty: payload.qty,
      price: payload.price ?? 0,
      status: payload.type === "MARKET" ? "FILLED" : "WORKING",
    });
    return ok({
      order_id: mock.mockOrders.length,
      trace_id: "manual:mock",
      status: "FILLED",
      position_id: null,
      trade_id: null,
    });
  }),
  http.get("/api/trades", async () => {
    await delay(LATENCY);
    return ok(mock.mockTrades.map(wire.toWireTrade));
  }),

  // ---------- AI 决策 / 事件 ----------
  http.get("/api/decisions", async () => {
    await delay(LATENCY);
    return ok(mock.mockDecisions.map(wire.toWireDecision));
  }),
  http.get("/api/decisions/:id", async ({ params }) => {
    await delay(LATENCY);
    const d = mock.mockDecisions.find(
      (x) => String(Number(x.id.replace(/\D/g, "")) || 1) === params.id,
    );
    return ok(d ? wire.toWireDecisionDetail(d) : null);
  }),
  http.get("/api/events/catchup", async () => {
    await delay(LATENCY);
    return ok(wire.toWireCatchup(mock.mockEvents));
  }),

  // ---------- 行情 ----------
  http.get("/api/market/symbols", async () => {
    await delay(LATENCY);
    return ok(mock.mockSymbols.map(wire.toWireMarketSymbol));
  }),
  http.get("/api/market/klines", async ({ request }) => {
    await delay(220);
    const url = new URL(request.url);
    const symbol = url.searchParams.get("symbol") ?? "BTCUSDT";
    const limit = Number(url.searchParams.get("limit") ?? 180);
    return ok(mock.genKlines(symbol, limit).map(wire.toWireKline));
  }),
  http.get("/api/market/ticker", async ({ request }) => {
    await delay(LATENCY);
    const symbol = new URL(request.url).searchParams.get("symbol") ?? "BTCUSDT";
    return ok(wire.toWireTicker(mock.genTicker(symbol)));
  }),
  // 盘口/逐笔走 /ws/market（marketStream.ts 的 mock 分支），无 REST 端点

  // ---------- 绩效 ----------
  http.get("/api/performance/summary", async () => {
    await delay(LATENCY);
    return ok(wire.toWirePerfSummary());
  }),
  http.get("/api/performance/monthly", async () => {
    await delay(LATENCY);
    return ok(mock.mockMonthlyPnl.map(wire.toWireMonthly));
  }),
  http.get("/api/performance/attribution", async ({ request }) => {
    await delay(LATENCY);
    const dim = new URL(request.url).searchParams.get("dim") ?? "symbol";
    return ok(wire.wireAttribution(dim));
  }),

  // ---------- 策略与风控 ----------
  http.get("/api/strategies", async () => {
    await delay(LATENCY);
    return ok(mock.mockStrategies.map((s) => ({ ...s })));
  }),
  http.patch("/api/strategies/:id", async ({ params, request }) => {
    await delay(250);
    const body = (await request.json()) as { enabled: boolean };
    const s = mock.mockStrategies.find((x) => x.id === params.id);
    if (s) s.enabled = body.enabled;
    return ok({ ok: true });
  }),
  http.get("/api/risk/limits", async () => {
    await delay(LATENCY);
    return ok({ ...wire.wireRiskLimits });
  }),
  http.get("/api/admin/symbols", async () => {
    await delay(LATENCY);
    return ok(mock.mockSymbolConfigs.map((s) => ({ ...s })));
  }),

  // ---------- 策略实验室 ----------
  http.get("/api/lab/candidates", async () => {
    await delay(LATENCY);
    return ok(mock.mockLabCandidates.map(wire.toWireLabCandidate));
  }),
  http.get("/api/lab/history", async () => {
    await delay(LATENCY);
    return ok(mock.mockLabHistory.map(wire.toWireLabHistory));
  }),
  http.post("/api/lab/candidates/:id/start", async ({ params }) => {
    await delay(350);
    const c = mock.mockLabCandidates.find((x) => x.id === params.id);
    if (c) {
      c.stage = "shadow";
      c.shadowProgressPct = 2;
      c.shadowDays = 0;
      c.blockReason = "影子期进度 2% < 60%，继续观察";
      c.promotable = false;
    }
    return ok({ ok: true });
  }),
  http.post("/api/lab/candidates/:id/promote", async ({ params }) => {
    await delay(400);
    const c = mock.mockLabCandidates.find((x) => x.id === params.id);
    if (c) c.stage = "canary";
    return ok({ ok: true });
  }),
  http.post("/api/lab/candidates/:id/terminate", async ({ params }) => {
    await delay(350);
    const i = mock.mockLabCandidates.findIndex((x) => x.id === params.id);
    if (i >= 0) {
      const [c] = mock.mockLabCandidates.splice(i, 1);
      mock.mockLabHistory.unshift({
        ts: "刚刚",
        kind: "retire",
        title: `${c.title.slice(0, 20)}… 终止归档`,
        note: "人工终止",
      });
    }
    return ok({ ok: true });
  }),

  // ---------- 审计 / 报告 ----------
  http.get("/api/admin/audit-logs", async () => {
    await delay(LATENCY);
    return ok(mock.mockAuditLogs.map(wire.toWireAuditLog));
  }),
  http.get("/api/reports", async () => {
    await delay(LATENCY);
    return ok(mock.mockReports.map(wire.toWireReport));
  }),

  // ---------- Agent（chat 流在 agentStream.ts mock 分支，不走 MSW） ----------
  http.get("/api/agent/history", async () => {
    await delay(LATENCY);
    return ok([]);
  }),
  http.post("/api/agent/actions/:id/confirm", async ({ params }) => {
    await delay(400);
    return ok({
      action_id: Number(params.id),
      status: "applied",
      key: "MAX_DAILY_LOSS_PCT",
      value: "2",
    });
  }),

  // ---------- 用户 / RBAC ----------
  http.get("/api/admin/users", async () => {
    await delay(LATENCY);
    return ok(mock.mockUsers.map(wire.toWireUser));
  }),
  http.get("/api/admin/roles", async () => {
    await delay(LATENCY);
    return ok(wire.toWireRoles(mock.mockPermissions, "owner"));
  }),
  http.post("/api/admin/users/:id/approve", async ({ params }) => {
    await delay(300);
    const u = mock.mockUsers.find((x) => x.id === params.id);
    if (u) u.status = "active";
    return ok({ ok: true });
  }),

  // ---------- 认证（会话用 sessionStorage 模拟 httpOnly cookie） ----------
  http.post("/api/auth/login", async ({ request }) => {
    await delay(400);
    const body = (await request.json()) as { email: string; password: string };
    if (!body.email || !body.password) {
      return HttpResponse.json({
        success: false,
        code: "AUTH_INVALID",
        message: "邮箱或密码错误",
        data: null,
      });
    }
    sessionStorage.setItem("ap.mock.authed", "1");
    return ok({
      access_token: "mock-token",
      token_type: "bearer",
      user: wire.toWireUser(mock.mockUsers[0]),
      requires_2fa: false,
      two_fa_token: null,
    });
  }),
  http.post("/api/auth/2fa/login", async () => {
    await delay(300);
    sessionStorage.setItem("ap.mock.authed", "1");
    return ok({
      access_token: "mock-token",
      token_type: "bearer",
      user: wire.toWireUser(mock.mockUsers[0]),
      requires_2fa: false,
      two_fa_token: null,
    });
  }),
  http.get("/api/auth/me", async () => {
    await delay(80);
    if (sessionStorage.getItem("ap.mock.authed") !== "1") {
      return HttpResponse.json(
        { success: false, code: "UNAUTHORIZED", message: "未登录", data: null },
        { status: 401 },
      );
    }
    return ok(wire.toWireUser(mock.mockUsers[0]));
  }),
  http.post("/api/auth/logout", async () => {
    await delay(120);
    sessionStorage.removeItem("ap.mock.authed");
    return ok({ ok: true });
  }),

  // ---------- 设置（P4，模块态持久到会话内） ----------
  http.get("/api/settings/exchange", async () => {
    await delay(LATENCY);
    return ok({ ...settingsState.exchange });
  }),
  http.put("/api/settings/exchange", async ({ request }) => {
    await delay(300);
    const b = (await request.json()) as {
      network?: string;
      api_key?: string;
    };
    if (b.network === "mainnet" || b.network === "testnet")
      settingsState.exchange.network = b.network;
    if (b.api_key)
      settingsState.exchange.api_key_masked = `****${b.api_key.slice(-4)}`;
    settingsState.exchange.has_secret = true;
    return ok({ ...settingsState.exchange });
  }),
  http.post("/api/settings/exchange/test", async () => {
    await delay(1000);
    return ok({
      ok: true,
      permissions: { read: true, trade: true, withdraw: false },
      warning: null,
      error: null,
    });
  }),
  http.get("/api/settings/llm", async () => {
    await delay(LATENCY);
    return ok({ ...settingsState.llm });
  }),
  http.put("/api/settings/llm", async ({ request }) => {
    await delay(300);
    const b = (await request.json()) as Record<string, unknown>;
    const llm = settingsState.llm;
    if (typeof b.model === "string") llm.model = b.model;
    if (typeof b.base_url === "string") llm.base_url = b.base_url;
    if (typeof b.api_key === "string" && b.api_key)
      llm.api_key_masked = `****${(b.api_key as string).slice(-4)}`;
    if (typeof b.temperature === "number") llm.temperature = b.temperature;
    if (typeof b.timeout_seconds === "number")
      llm.timeout_seconds = b.timeout_seconds;
    return ok({ ...llm });
  }),
  http.post("/api/settings/llm/test", async () => {
    await delay(900);
    return ok({ ok: true, latency_ms: 842, error: null });
  }),
  http.get("/api/settings/notifications", async () => {
    await delay(LATENCY);
    return ok({ ...settingsState.notify });
  }),
  http.put("/api/settings/notifications", async ({ request }) => {
    await delay(250);
    const b = (await request.json()) as {
      channels?: Record<string, boolean>;
      subscriptions?: Record<string, boolean>;
    };
    if (b.channels)
      settingsState.notify.channels = { ...settingsState.notify.channels, ...b.channels };
    if (b.subscriptions)
      settingsState.notify.subscriptions = {
        ...settingsState.notify.subscriptions,
        ...b.subscriptions,
      };
    return ok({ ...settingsState.notify });
  }),

  // ---------- 命令 ----------
  http.post("/api/commands/close-all", async () => {
    await delay(600);
    mock.mockPositions.splice(0, mock.mockPositions.length);
    return ok({ taskId: "task_mock_1" });
  }),
  http.post("/api/commands/pause", async () => {
    await delay(300);
    return ok({ ok: true });
  }),
  http.post("/api/commands/resume", async () => {
    await delay(300);
    return ok({ ok: true });
  }),
];
