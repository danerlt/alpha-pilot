/**
 * 领域 mock 数据 → wire 形状（真实后端契约）。仅 MSW handlers 使用，
 * 保证 mock 响应与真实后端字节级同构（adapter 全链路被 mock 覆盖）。
 */
import type {
  Decision,
  Kline,
  MarketSymbol,
  PermissionRow,
  Position,
  RiskState,
  Ticker,
  Trade,
  User,
} from "../types";
import type {
  WireDecision,
  WireDecisionDetail,
  WireKline,
  WireMarketSymbol,
  WirePosition,
  WireRiskState,
  WireRoles,
  WireTicker,
  WireTrade,
  WireUser,
} from "../wire";
import { mockAccount } from "../mock/data";

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
  };
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
    confidence: d.confidence,
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

export function toWireUser(u: User): WireUser {
  return {
    id: Number(u.id.replace(/\D/g, "")) || 1,
    username: u.name,
    email: u.email,
    role: u.role,
    status: u.status,
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
