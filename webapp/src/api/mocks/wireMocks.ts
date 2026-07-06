/**
 * 领域 mock 数据 → wire 形状（真实后端契约）。仅 MSW handlers 使用，
 * 保证 mock 响应与真实后端字节级同构（adapter 全链路被 mock 覆盖）。
 */
import type {
  Decision,
  EventItem,
  Kline,
  LabCandidate,
  LabHistoryItem,
  MarketSymbol,
  MonthlyPnl,
  Order,
  PermissionRow,
  Position,
  RiskState,
  Ticker,
  Trade,
  User,
} from "../types";
import type {
  WireAttribution,
  WireCatchup,
  WireDecision,
  WireDecisionDetail,
  WireKline,
  WireMarketSymbol,
  WireMonthlyPnl,
  WireOrder,
  WirePerfSummary,
  WirePosition,
  WireRiskLimits,
  WireRiskState,
  WireRoles,
  WireTicker,
  WireTrade,
  WireUser,
} from "../wire";
import { mockAccount, mockAttribution, mockPerformance } from "../mock/data";

function isoToday(hms: string): string {
  const d = new Date();
  const [h = "0", m = "0", s = "0"] = hms.split(":");
  d.setHours(Number(h), Number(m), Number(s), 0);
  return d.toISOString();
}

export function toWireRiskState(r: RiskState): WireRiskState {
  return {
    state: r.state,
    day_loss_pct: r.dayLossPct,
    positions_pct: r.positionsPct,
    regime: r.regime,
  };
}

export function toWireAccount() {
  return {
    total_balance_usdt: mockAccount.equity,
    available_balance_usdt: mockAccount.equity * 0.85,
    unrealized_pnl: 52.82,
    daily_pnl: mockAccount.todayPnl,
    daily_pnl_pct: mockAccount.todayPnlPct,
    snapshot_at: new Date().toISOString(),
    message: null,
  };
}

export function toWirePosition(p: Position): WirePosition {
  return {
    id: Number(p.id.replace(/\D/g, "")) || 1,
    symbol: p.symbol,
    quantity: p.qty,
    entry_price: p.entry,
    current_price: p.mark,
    stop_loss: p.sl,
    take_profit: p.tp,
    unrealized_pnl: p.pnl,
    unrealized_pnl_pct: p.pnlPct,
    opened_at: new Date(Date.now() - 2 * 3_600_000).toISOString(),
    strategy_mode: p.strategy,
    position_pct: p.marginPct,
  } as WirePosition;
}

export function toWireTrade(t: Trade): WireTrade {
  return {
    id: Number(t.id.replace(/\D/g, "")) || 1,
    symbol: t.symbol,
    quantity: t.qty,
    entry_price: t.entry,
    exit_price: t.exit ?? t.entry,
    pnl: t.pnl ?? 0,
    pnl_pct: t.pnlPct ?? 0,
    exit_reason: t.exitType ?? "AI",
    strategy_mode: t.strategy,
    opened_at: new Date(Date.now() - 5 * 3_600_000).toISOString(),
    closed_at: new Date(Date.now() - 3 * 3_600_000).toISOString(),
    holding_seconds: 7200,
  } as WireTrade;
}

export function toWireDecision(d: Decision): WireDecision {
  return {
    id: Number(d.id.replace(/\D/g, "")) || 1,
    symbol: d.symbol,
    timeframe: d.timeframe,
    action: d.action,
    guard_verdict: d.guard,
    confidence: d.confidence,
    entry_price: d.entry ?? null,
    stop_loss: d.sl ?? null,
    take_profit: d.tp ?? null,
    position_size_pct: d.sizePct ? parseFloat(d.sizePct) : null,
    strategy_mode: d.strategy,
    reasoning: [d.reason],
    risk_note: null,
    is_fallback: d.guard === "DEGRADE",
    decided_at: isoToday(d.ts),
  } as WireDecision;
}

export function toWireDecisionDetail(d: Decision): WireDecisionDetail {
  return {
    ...toWireDecision(d),
    entry_type: "MARKET",
    entry_price: d.entry ?? null,
    stop_loss: d.sl ?? null,
    take_profit: d.tp ?? null,
    position_size_pct: d.sizePct ? parseFloat(d.sizePct) : null,
    source: "ai",
    llm_provider: "deepseek",
    llm_model: "deepseek-v4-pro",
    tokens_used: 1820,
    latency_ms: 940,
    features: Object.fromEntries((d.features ?? []).map((f) => [f.k, f.v])),
    reviews: [],
    guard_events: (d.guards ?? [])
      .filter((g) => !g.ok)
      .map((g, i) => ({
        id: i + 1,
        event_type: g.k,
        description: g.note,
        triggered_at: isoToday(d.ts),
        resolved: false,
      })),
    orders: [],
    position_ids: [],
  } as unknown as WireDecisionDetail;
}

export function toWireMarketSymbol(s: MarketSymbol): WireMarketSymbol {
  return {
    symbol: s.symbol,
    base_asset: s.symbol.replace("USDT", ""),
    last_price: s.price,
    price_change_pct: s.changePct24h,
    quote_volume_24h: s.volume24h,
    has_position: s.hasPosition,
    regime: s.regime,
  };
}

export function toWireKline(k: Kline): WireKline {
  return {
    open_time: new Date(k.t).toISOString(),
    open: k.o,
    high: k.h,
    low: k.l,
    close: k.c,
    volume: k.v,
  };
}

export function toWireTicker(t: Ticker): WireTicker {
  return {
    symbol: t.symbol,
    last_price: t.markPrice,
    price_change_pct: null,
    high_24h: t.high24h,
    low_24h: t.low24h,
    volume_24h: t.volume24h,
    quote_volume_24h: null,
    mark_price: t.markPrice,
    index_price: t.indexPrice,
    funding_rate: t.fundingRate,
    next_funding_time: new Date(Date.now() + 3 * 3_600_000).toISOString(),
    open_interest: t.openInterest,
  };
}

export function toWireOrder(o: Order): WireOrder {
  return {
    id: Number(o.id.replace(/\D/g, "")) || 1,
    symbol: o.symbol,
    side: o.side,
    order_type: o.type,
    status: o.status,
    quantity: o.qty,
    price: o.price,
    avg_fill_price: o.status === "FILLED" ? o.price : null,
    trace_id: `manual:mock:${o.id}`,
    position_id: null,
    ai_decision_id: null,
    submitted_at: isoToday(o.ts.includes(":") ? o.ts : "14:23:09"),
    filled_at: o.status === "FILLED" ? isoToday("14:23:09") : null,
  } as WireOrder;
}

export function toWireCatchup(events: EventItem[]): WireCatchup {
  return {
    events: events.map((e) => ({
      event_id: e.id,
      event_type: `mock.${e.kind}`,
      envelope: {
        event_id: e.id,
        event_type: `mock.${e.kind}`,
        occurred_at: isoToday(e.ts),
        payload: { message: e.msg },
      },
    })),
    count: events.length,
    limit: 200,
  } as unknown as WireCatchup;
}

export const wireRiskLimits: WireRiskLimits = {
  max_position_size_pct: 20,
  max_daily_loss_pct: 3,
  max_consecutive_losses: 3,
  max_single_risk_pct: 1,
  min_rr_ratio: 1.5,
  sl_atr_min_mult: 1.0,
  sl_atr_max_mult: 3.0,
};

export function toWirePerfSummary(): WirePerfSummary {
  const p = mockPerformance;
  const base = 110000;
  return {
    range_days: 90,
    net_return_pct: p.netReturnPct,
    hodl_return_pct: p.hodlBtcReturnPct,
    vs_hodl_pct: p.netReturnPct - p.hodlBtcReturnPct,
    sharpe: p.sharpe,
    sortino: p.sortino,
    max_drawdown_pct: p.maxDD,
    win_rate: p.winRate,
    profit_factor: p.profitFactor,
    trades: 85,
    net_pnl: 8934.5,
    today_trades: 7,
    avg_holding_seconds: 8040,
    week_pnl: 5420.11,
    month_pnl: 8934.5,
    // 后端 curve 为绝对权益 + 归一 HODL；由 mock 百分比曲线反推
    curve: p.curve.map((c) => ({
      ts: c.ts,
      equity: base * (1 + c.strategy / 100),
      hodl: base * (1 + c.hodl / 100),
    })),
  };
}

export function toWireMonthly(m: MonthlyPnl): WireMonthlyPnl {
  return { month: m.month, pnl: m.pnl, trades: m.trades ?? 12 };
}

export function wireAttribution(dim: string): WireAttribution[] {
  return (mockAttribution[dim] ?? []).map((r) => ({
    key: r.key,
    trades: r.trades,
    net_pnl: r.pnl,
    win_rate: r.winRate,
  }));
}

function parsePct(v: string | number): number | null {
  if (typeof v === "number") return v;
  const n = parseFloat(v.replace("%", ""));
  return Number.isNaN(n) ? null : n;
}

export function toWireLabCandidate(c: LabCandidate) {
  const get = (k: string) => c.metrics.find((m) => m.k.includes(k));
  const trades = get("交易数");
  const pnl = get("净收益");
  const wr = get("胜率");
  const wrNum = (v: string | number | undefined) => {
    const n = v == null ? null : parsePct(v);
    return n == null ? null : n / 100;
  };
  return {
    id: Number(c.id.replace(/\D/g, "")) || 1,
    name: c.title,
    description: null,
    source: c.source,
    stage: c.stage,
    params: {},
    shadow_progress: c.shadowProgressPct / 100,
    shadow_days_target: 14,
    shadow_started_at: c.stage === "queued" ? null : isoToday("09:00:00"),
    promote_eligible: c.promotable,
    promote_blocked_reason: c.blockReason ?? null,
    metrics: {
      shadow: {
        decisions: typeof trades?.shadow === "number" ? trades.shadow : 0,
        simulated_pnl_pct: pnl ? parsePct(pnl.shadow) : null,
        win_rate: wrNum(wr?.shadow),
      },
      live: {
        trades: typeof trades?.live === "number" ? trades.live : 0,
        net_pnl_pct: pnl ? parsePct(pnl.live) : null,
        win_rate: wrNum(wr?.live),
      },
    },
    rollback_reason: null,
    created_at: `${c.createdAt}T09:00:00Z`,
  };
}

export function toWireLabHistory(h: LabHistoryItem) {
  return {
    action: h.kind,
    candidate_id: 1,
    candidate_name: h.title,
    stage: h.kind === "promote" ? "live" : "retired",
    reason: h.note ?? null,
    operator: "admin",
    at: `${h.ts}T09:00:00Z`,
  };
}

export function toWireUser(u: User): WireUser {
  return {
    id: Number(u.id.replace(/\D/g, "")) || 1,
    username: u.name,
    email: u.email,
    role: u.role,
    status: u.status,
    two_fa_enabled: u.twoFa,
  } as WireUser;
}

export function toWireRoles(rows: PermissionRow[], currentRole: string): WireRoles {
  const groups: Record<string, PermissionRow[]> = {};
  for (const r of rows) (groups[r.group] ??= []).push(r);
  return {
    roles: ["owner", "admin", "trader", "viewer"],
    matrix: Object.entries(groups).map(([group, items]) => ({
      group,
      items: items.map((it) => ({
        key: it.key,
        label: it.label,
        owner: it.granted.owner,
        admin: it.granted.admin,
        trader: it.granted.trader,
        viewer: it.granted.viewer,
      })),
    })),
    role_aliases: { user: "trader" },
    current_role: currentRole,
  } as WireRoles;
}
