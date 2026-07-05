/**
 * MSW handlers —— dev（无后端）与测试共用的网络层 mock。
 * 响应形状与后端统一响应包严格一致（{success, code, message, data}），
 * 对应真实端点落地后：删除这里的 handler 即可，业务代码零改动。
 */
import { HttpResponse, delay, http } from "msw";
import type { OrderTicketPayload } from "../types";
import * as mock from "../mock/data";

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

export const handlers = [
  // ---------- 风控 / 账户 ----------
  http.get("/api/risk/state", async () => {
    await delay(LATENCY);
    return ok({ ...mock.mockRiskState });
  }),
  http.get("/api/account", async () => {
    await delay(LATENCY);
    return ok({ ...mock.mockAccount });
  }),
  http.get("/api/account/history", async () => {
    await delay(LATENCY);
    return ok([...mock.mockEquitySeries]);
  }),

  // ---------- 持仓 / 订单 / 交易 ----------
  http.get("/api/positions", async () => {
    await delay(LATENCY);
    return ok(mock.mockPositions.map((p) => ({ ...p })));
  }),
  http.post("/api/commands/close-position/:id", async ({ params }) => {
    await delay(400);
    const i = mock.mockPositions.findIndex((p) => p.id === params.id);
    if (i >= 0) mock.mockPositions.splice(i, 1);
    return ok({ ok: true });
  }),
  http.patch("/api/positions/:id/sltp", async ({ params, request }) => {
    await delay(300);
    const body = (await request.json()) as { sl: number; tp: number };
    const p = mock.mockPositions.find((x) => x.id === params.id);
    if (p) {
      p.sl = body.sl;
      p.tp = body.tp;
    }
    return ok({ ok: true });
  }),
  http.get("/api/orders", async () => {
    await delay(LATENCY);
    return ok(mock.mockOrders.map((o) => ({ ...o })));
  }),
  http.post("/api/orders/precheck", async ({ request }) => {
    await delay(350);
    const payload = (await request.json()) as OrderTicketPayload;
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
    return ok({ verdict: pass ? "PASS" : "REJECT", items });
  }),
  http.post("/api/orders", async ({ request }) => {
    await delay(500);
    const payload = (await request.json()) as OrderTicketPayload;
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
    return ok({ ok: true });
  }),
  http.get("/api/trades", async () => {
    await delay(LATENCY);
    return ok(mock.mockTrades.map((t) => ({ ...t })));
  }),

  // ---------- AI 决策 / 事件 ----------
  http.get("/api/decisions", async () => {
    await delay(LATENCY);
    return ok(mock.mockDecisions.map((d) => ({ ...d })));
  }),
  http.get("/api/decisions/:id", async ({ params }) => {
    await delay(LATENCY);
    return ok(mock.mockDecisions.find((d) => d.id === params.id) ?? null);
  }),
  http.get("/api/events/catchup", async () => {
    await delay(LATENCY);
    return ok(mock.mockEvents.map((e) => ({ ...e })));
  }),

  // ---------- 行情 ----------
  http.get("/api/market/symbols", async () => {
    await delay(LATENCY);
    return ok(mock.mockSymbols.map((s) => ({ ...s })));
  }),
  http.get("/api/market/klines", async ({ request }) => {
    await delay(220);
    const url = new URL(request.url);
    const symbol = url.searchParams.get("symbol") ?? "BTCUSDT";
    const limit = Number(url.searchParams.get("limit") ?? 180);
    return ok(mock.genKlines(symbol, limit));
  }),
  http.get("/api/market/ticker", async ({ request }) => {
    await delay(LATENCY);
    const symbol = new URL(request.url).searchParams.get("symbol") ?? "BTCUSDT";
    return ok(mock.genTicker(symbol));
  }),
  http.get("/api/market/depth", async ({ request }) => {
    await delay(120);
    const symbol = new URL(request.url).searchParams.get("symbol") ?? "BTCUSDT";
    return ok(mock.genOrderBook(symbol));
  }),
  http.get("/api/market/trades", async ({ request }) => {
    await delay(120);
    const symbol = new URL(request.url).searchParams.get("symbol") ?? "BTCUSDT";
    return ok(mock.genRecentTrades(symbol));
  }),

  // ---------- 绩效 ----------
  http.get("/api/performance/summary", async () => {
    await delay(LATENCY);
    return ok({ ...mock.mockPerformance });
  }),
  http.get("/api/performance/monthly", async () => {
    await delay(LATENCY);
    return ok([...mock.mockMonthlyPnl]);
  }),
  http.get("/api/performance/attribution", async ({ request }) => {
    await delay(LATENCY);
    const dim = new URL(request.url).searchParams.get("dim") ?? "symbol";
    return ok([...(mock.mockAttribution[dim] ?? [])]);
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
  http.get("/api/config/runtime", async () => {
    await delay(LATENCY);
    return ok([...mock.mockHardLimits]);
  }),
  http.get("/api/admin/symbols", async () => {
    await delay(LATENCY);
    return ok(mock.mockSymbolConfigs.map((s) => ({ ...s })));
  }),

  // ---------- 策略实验室 ----------
  http.get("/api/lab/candidates", async () => {
    await delay(LATENCY);
    return ok(mock.mockLabCandidates.map((c) => ({ ...c })));
  }),
  http.get("/api/lab/history", async () => {
    await delay(LATENCY);
    return ok([...mock.mockLabHistory]);
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
    return ok(mock.mockAuditLogs.map((a) => ({ ...a })));
  }),
  http.get("/api/reports", async () => {
    await delay(LATENCY);
    return ok(mock.mockReports.map((r) => ({ ...r })));
  }),

  // ---------- 用户 / RBAC ----------
  http.get("/api/admin/users", async () => {
    await delay(LATENCY);
    return ok(mock.mockUsers.map((u) => ({ ...u })));
  }),
  http.get("/api/admin/roles", async () => {
    await delay(LATENCY);
    return ok([...mock.mockPermissions]);
  }),
  http.post("/api/admin/users/:id/approve", async ({ params }) => {
    await delay(300);
    const u = mock.mockUsers.find((x) => x.id === params.id);
    if (u) u.status = "active";
    return ok({ ok: true });
  }),

  // ---------- 认证（S3 接线用） ----------
  http.post("/api/auth/login", async () => {
    await delay(400);
    return ok({ ...mock.mockUsers[0] });
  }),
  http.get("/api/auth/me", async () => {
    await delay(80);
    return ok({ ...mock.mockUsers[0] });
  }),
  http.post("/api/auth/logout", async () => {
    await delay(120);
    return ok({ ok: true });
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
