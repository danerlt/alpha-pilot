/**
 * Mock 数据集 —— 形状与设计稿 ui_kits/web_app 的 W_MOCK 对齐，
 * 数值仅用于视觉联调，后端就绪后整个 mock 目录可删除。
 */
import type {
  AccountOverview,
  AccountSnapshot,
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
  PerformanceSummary,
  PermissionRow,
  Position,
  RecentTrade,
  RiskState,
  StrategyCard,
  SymbolConfig,
  Ticker,
  Trade,
  User,
} from "../types";

// ---------- 全局风控 ----------
export const mockRiskState: RiskState = {
  state: "OK",
  dayLossPct: -0.48,
  positionsPct: 12,
  regime: "trending_up",
};

// ---------- 账户 ----------
export const mockAccount: AccountOverview = {
  equity: 128450.73,
  equityChange: 2291.4,
  equityChangePct: 1.82,
  todayPnl: 1248.05,
  todayPnlPct: 0.98,
  weekPnl: 5420.11,
  weekPnlPct: 4.32,
  mtdPnl: 8934.5,
  mtdPnlPct: 7.45,
  tradesToday: 7,
  winRate: 57,
  sharpe: 1.84,
  maxDD: -4.23,
  avgHold: "2h 14m",
};

/** 确定性伪随机（可复现，避免每次渲染跳动） */
function seeded(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
}

export const mockEquitySeries: AccountSnapshot[] = (() => {
  const rnd = seeded(42);
  const out: AccountSnapshot[] = [];
  let eq = 120000;
  for (let i = 0; i < 96; i++) {
    eq += (rnd() - 0.44) * 620;
    const h = String(Math.floor(i / 4)).padStart(2, "0");
    const m = String((i % 4) * 15).padStart(2, "0");
    out.push({ ts: `${h}:${m}`, equity: Math.round(eq * 100) / 100 });
  }
  out[out.length - 1] = { ...out[out.length - 1], equity: mockAccount.equity };
  return out;
})();

// ---------- 持仓 / 订单 / 交易 ----------
export const mockPositions: Position[] = [
  {
    id: "p_01",
    symbol: "BTCUSDT",
    side: "LONG",
    qty: 0.048,
    entry: 67420.5,
    mark: 68863.92,
    pnl: 69.29,
    pnlPct: 2.14,
    marginPct: 2.5,
    sl: 64210,
    tp: 68900,
    age: "2h 13m",
    strategy: "趋势跟随",
  },
  {
    id: "p_02",
    symbol: "ETHUSDT",
    side: "LONG",
    qty: 0.82,
    entry: 3240.0,
    mark: 3219.92,
    pnl: -16.47,
    pnlPct: -0.62,
    marginPct: 1.8,
    sl: 3120,
    tp: 3380,
    age: "45m",
    strategy: "突破确认",
  },
];

export const mockOrders: Order[] = [
  { id: "o_1", ts: "14:23:09", symbol: "BTCUSDT", side: "BUY", type: "MARKET", qty: 0.048, price: 67420.5, status: "FILLED" },
  { id: "o_2", ts: "14:23:09", symbol: "BTCUSDT", side: "SELL", type: "STOP", qty: 0.048, price: 64210, status: "WORKING" },
  { id: "o_3", ts: "14:23:09", symbol: "BTCUSDT", side: "SELL", type: "TAKE_PROFIT", qty: 0.048, price: 68900, status: "WORKING" },
  { id: "o_4", ts: "13:45:12", symbol: "ETHUSDT", side: "BUY", type: "LIMIT", qty: 0.82, price: 3240, status: "FILLED" },
  { id: "o_5", ts: "10:15:30", symbol: "BTCUSDT", side: "SELL", type: "MARKET", qty: 0.062, price: 68903.2, status: "FILLED" },
];

export const mockTrades: Trade[] = [
  { id: "t_1", ts: "10:15:30", symbol: "BTCUSDT", action: "CLOSE_LONG", qty: 0.062, entry: 66100, exit: 68903.2, pnl: 173.8, pnlPct: 1.82, exitType: "TP", strategy: "止盈执行" },
  { id: "t_2", ts: "昨天 22:40", symbol: "ETHUSDT", action: "CLOSE_LONG", qty: 1.2, entry: 3305, exit: 3266.4, pnl: -46.3, pnlPct: -1.17, exitType: "SL", strategy: "突破确认" },
  { id: "t_3", ts: "昨天 16:02", symbol: "BTCUSDT", action: "CLOSE_LONG", qty: 0.05, entry: 65210, exit: 66480, pnl: 63.5, pnlPct: 1.95, exitType: "AI", strategy: "趋势跟随" },
];

// ---------- AI 决策 ----------
export const mockDecisions: Decision[] = [
  {
    id: "d_7f3a9b",
    ts: "14:23:08",
    symbol: "BTCUSDT",
    timeframe: "15m",
    action: "OPEN_LONG",
    confidence: 0.78,
    strategy: "趋势跟随",
    sl: 64210,
    tp: 68900,
    sizePct: "2.5%",
    guard: "PASS",
    entry: 67420.5,
    reason:
      "EMA20>EMA50>EMA200 金叉排列，1h 成交量较均值放大 1.4x，回踩 EMA20 未破，确认突破有效。",
    features: [
      { k: "regime", v: "trending_up", ok: true },
      { k: "EMA_align", v: "20>50>200", ok: true },
      { k: "vol_mult", v: "1.4x", ok: true },
      { k: "ATR_14", v: "1.82%", ok: true },
      { k: "RSI_14", v: "58", ok: true },
      { k: "BB_width", v: "0.043", ok: true },
    ],
    guards: [
      { k: "regime_match", ok: true, note: "trending_up ∈ strategy.allowed" },
      { k: "max_per_trade_risk", ok: true, note: "0.8% < 1.0%" },
      { k: "max_position_size", ok: true, note: "2.5% < 15%" },
      { k: "daily_loss_limit", ok: true, note: "-0.48% > -2.0%" },
      { k: "RR_ratio", ok: true, note: "2.3 > 1.5" },
      { k: "correlation_cap", ok: true, note: "BTC-ETH corr 0.68 < 0.85" },
      { k: "spread_check", ok: true, note: "1.2bps < 5bps" },
      { k: "cooldown", ok: true, note: "last trade 3h ago" },
    ],
  },
  {
    id: "d_7f3a9a",
    ts: "13:45:00",
    symbol: "ETHUSDT",
    timeframe: "15m",
    action: "HOLD",
    confidence: 0.42,
    strategy: "观望模式",
    guard: "DEGRADE",
    reason:
      "波动率进入高位，regime 由 trending_up 切换为 chaotic，降级为观望。",
    features: [
      { k: "regime", v: "chaotic", ok: false },
      { k: "ATR_14", v: "3.4%", ok: false },
      { k: "RSI_14", v: "49", ok: true },
      { k: "vol_mult", v: "2.1x", ok: false },
    ],
    guards: [
      { k: "regime_match", ok: false, note: "chaotic → DEGRADE" },
      { k: "daily_loss_limit", ok: true, note: "-0.48% > -2.0%" },
    ],
  },
  {
    id: "d_7f3a99",
    ts: "12:30:00",
    symbol: "BTCUSDT",
    timeframe: "15m",
    action: "OPEN_LONG",
    confidence: 0.71,
    strategy: "突破确认",
    guard: "REJECT",
    reason: "触发风险收益比 <1.5 检查，守卫拒绝，回退 HOLD。",
    guards: [
      { k: "RR_ratio", ok: false, note: "1.2 < 1.5" },
      { k: "max_position_size", ok: true, note: "3.0% < 15%" },
    ],
  },
  {
    id: "d_7f3a98",
    ts: "10:15:00",
    symbol: "BTCUSDT",
    timeframe: "15m",
    action: "CLOSE_LONG",
    confidence: 0.85,
    strategy: "止盈执行",
    guard: "PASS",
    reason: "达到 TP 价位，执行平仓，本笔 +1.82%。",
    entry: 66100,
  },
  {
    id: "d_7f3a97",
    ts: "09:02:00",
    symbol: "ETHUSDT",
    timeframe: "15m",
    action: "OPEN_LONG",
    confidence: 0.66,
    strategy: "突破确认",
    guard: "PASS",
    reason: "突破前高 3240，成交量放大，进场。",
  },
];

// ---------- 事件流 ----------
export const mockEvents: EventItem[] = [
  { id: "e_1", ts: "14:23:09", kind: "fill", msg: "BTCUSDT 市价成交 0.048 @ 67,420.50", tone: "mint" },
  { id: "e_2", ts: "14:23:09", kind: "order", msg: "止损挂单 64,210 · 止盈 68,900", tone: "fg" },
  { id: "e_3", ts: "14:23:08", kind: "guard", msg: "守卫通过 PASS · 检查 8/8", tone: "mint" },
  { id: "e_4", ts: "14:23:08", kind: "ai", msg: "AI OPEN_LONG BTCUSDT · 置信度 0.78", tone: "violet" },
  { id: "e_5", ts: "13:45:05", kind: "guard", msg: "守卫降级 DEGRADE · regime 异常", tone: "amber" },
  { id: "e_6", ts: "13:45:00", kind: "ai", msg: "AI HOLD ETHUSDT · 置信度 0.42", tone: "violet" },
  { id: "e_7", ts: "12:30:12", kind: "guard", msg: "守卫拒绝 REJECT · RR<1.5 · 回退 HOLD", tone: "rose" },
  { id: "e_8", ts: "12:30:08", kind: "ai", msg: "AI OPEN_LONG BTCUSDT · 置信度 0.71", tone: "violet" },
  { id: "e_9", ts: "10:15:30", kind: "fill", msg: "BTCUSDT 平仓 @ 68,903 · +1.82%", tone: "mint" },
  { id: "e_10", ts: "10:15:29", kind: "ai", msg: "AI CLOSE_LONG BTCUSDT · 置信度 0.85", tone: "violet" },
  { id: "e_11", ts: "09:02:14", kind: "fill", msg: "ETHUSDT 市价成交 0.82 @ 3,240.00", tone: "mint" },
  { id: "e_12", ts: "09:02:10", kind: "ai", msg: "AI OPEN_LONG ETHUSDT · 置信度 0.66", tone: "violet" },
];

// ---------- 行情 ----------
export const mockSymbols: MarketSymbol[] = [
  { symbol: "BTCUSDT", price: 68863.92, changePct24h: 2.14, volume24h: 28_400_000_000, hasPosition: true, regime: "trending_up" },
  { symbol: "ETHUSDT", price: 3219.92, changePct24h: -0.62, volume24h: 12_100_000_000, hasPosition: true, regime: "ranging" },
  { symbol: "SOLUSDT", price: 142.35, changePct24h: 4.87, volume24h: 3_800_000_000, hasPosition: false, regime: "trending_up" },
  { symbol: "BNBUSDT", price: 585.2, changePct24h: 0.34, volume24h: 1_600_000_000, hasPosition: false, regime: "ranging" },
  { symbol: "XRPUSDT", price: 0.5234, changePct24h: -1.85, volume24h: 1_100_000_000, hasPosition: false, regime: "trending_down" },
  { symbol: "DOGEUSDT", price: 0.1245, changePct24h: 7.42, volume24h: 950_000_000, hasPosition: false, regime: "chaotic" },
];

const basePrice: Record<string, number> = {
  BTCUSDT: 68863.92,
  ETHUSDT: 3219.92,
  SOLUSDT: 142.35,
  BNBUSDT: 585.2,
  XRPUSDT: 0.5234,
  DOGEUSDT: 0.1245,
};

export function genKlines(symbol: string, n = 180): Kline[] {
  const base = basePrice[symbol] ?? 100;
  const rnd = seeded(symbol.split("").reduce((a, c) => a + c.charCodeAt(0), 7));
  const out: Kline[] = [];
  let c = base * 0.96;
  const t0 = 1_780_000_000_000; // 固定起点，保证可复现
  for (let i = 0; i < n; i++) {
    const o = c;
    const drift = (rnd() - 0.47) * base * 0.006;
    c = Math.max(o + drift, base * 0.8);
    const h = Math.max(o, c) + rnd() * base * 0.003;
    const l = Math.min(o, c) - rnd() * base * 0.003;
    out.push({
      t: t0 + i * 15 * 60 * 1000,
      o,
      h,
      l,
      c,
      v: 500 + rnd() * 2200,
    });
  }
  // 收敛到当前价
  out[out.length - 1] = { ...out[out.length - 1], c: base };
  return out;
}

export function genTicker(symbol: string): Ticker {
  const p = basePrice[symbol] ?? 100;
  return {
    symbol,
    high24h: p * 1.024,
    low24h: p * 0.972,
    volume24h: (mockSymbols.find((s) => s.symbol === symbol)?.volume24h ?? 0) / p,
    markPrice: p,
    indexPrice: p * 0.9998,
    fundingRate: 0.0001,
    openInterest: 83_412,
    nextFundingIn: "03:24:11",
  };
}

export function genOrderBook(symbol: string): OrderBook {
  const p = basePrice[symbol] ?? 100;
  const rnd = seeded(99);
  const tick = p > 1000 ? 0.5 : p > 10 ? 0.01 : 0.0001;
  const mk = (dir: 1 | -1) =>
    Array.from({ length: 12 }, (_, i) => ({
      price: p + dir * (i + 1) * tick * 4,
      qty: Math.round((0.2 + rnd() * 4) * 1000) / 1000,
    }));
  return { asks: mk(1), bids: mk(-1) };
}

export function genRecentTrades(symbol: string): RecentTrade[] {
  const p = basePrice[symbol] ?? 100;
  const rnd = seeded(7);
  return Array.from({ length: 20 }, (_, i) => ({
    ts: `14:2${3 - Math.floor(i / 10)}:${String(59 - i * 2).padStart(2, "0")}`,
    price: p * (1 + (rnd() - 0.5) * 0.001),
    qty: Math.round(rnd() * 900) / 1000,
    side: rnd() > 0.5 ? "BUY" : "SELL",
  }));
}

// ---------- 绩效 ----------
export const mockPerformance: PerformanceSummary = (() => {
  const rnd = seeded(2024);
  const curve: PerformanceSummary["curve"] = [];
  let strat = 0;
  let hodl = 0;
  for (let i = 0; i < 90; i++) {
    strat += (rnd() - 0.42) * 0.9;
    hodl += (rnd() - 0.46) * 1.3;
    curve.push({
      ts: `D${i + 1}`,
      strategy: Math.round(strat * 100) / 100,
      hodl: Math.round(hodl * 100) / 100,
    });
  }
  return {
    netReturnPct: 18.42,
    hodlBtcReturnPct: 11.07,
    sharpe: 1.84,
    sortino: 2.31,
    maxDD: -4.23,
    winRate: 57,
    profitFactor: 1.92,
    trades: 85,
    netPnl: 8934.5,
    todayTrades: 7,
    avgHold: "2h 14m",
    weekPnl: 5420.11,
    monthPnl: 8934.5,
    curve,
  };
})();

export const mockMonthlyPnl: MonthlyPnl[] = [
  { month: "1月", pnl: 2140 },
  { month: "2月", pnl: -860 },
  { month: "3月", pnl: 3320 },
  { month: "4月", pnl: 1105 },
  { month: "5月", pnl: -420 },
  { month: "6月", pnl: 3650 },
];

export const mockAttribution: Record<string, AttributionRow[]> = {
  symbol: [
    { key: "BTCUSDT", trades: 42, pnl: 6120.4, winRate: 61 },
    { key: "ETHUSDT", trades: 31, pnl: 1834.2, winRate: 52 },
    { key: "SOLUSDT", trades: 12, pnl: 980.1, winRate: 58 },
  ],
  strategy: [
    { key: "趋势跟随", trades: 48, pnl: 7215.6, winRate: 63 },
    { key: "突破确认", trades: 29, pnl: 1240.3, winRate: 48 },
    { key: "止盈执行", trades: 8, pnl: 478.8, winRate: 100 },
  ],
  trigger: [
    { key: "TP 止盈", trades: 35, pnl: 8420.5, winRate: 100 },
    { key: "SL 止损", trades: 28, pnl: -3105.2, winRate: 0 },
    { key: "AI 主动平仓", trades: 22, pnl: 3619.4, winRate: 68 },
  ],
};

// ---------- 策略与风控 ----------
export const mockStrategies: StrategyCard[] = [
  { id: "s_trend", name: "趋势跟随", enabled: true, regimes: ["trending_up"], desc: "EMA 多头排列 + 量能确认，回踩不破进场" },
  { id: "s_break", name: "突破确认", enabled: true, regimes: ["trending_up", "ranging"], desc: "关键位突破 + 二次确认，假突破过滤" },
  { id: "s_range", name: "区间反转", enabled: false, regimes: ["ranging"], desc: "布林带边界 + RSI 背离，仅限低波动区间" },
];

export const mockHardLimits: HardLimit[] = [
  { key: "MAX_POSITION_SIZE_PCT", label: "单仓位上限", value: "20%", desc: "任一持仓占权益比例上限" },
  { key: "MAX_DAILY_LOSS_PCT", label: "日亏损熔断", value: "3%", desc: "当日亏损超过即熔断，全天禁止开仓" },
  { key: "MAX_CONSECUTIVE_LOSSES", label: "连续亏损熔断", value: "3 笔", desc: "连续亏损达到阈值触发熔断" },
  { key: "MAX_SINGLE_RISK_PCT", label: "单笔风险上限", value: "1%", desc: "单笔交易最大可亏损占权益比例" },
];

export const mockSymbolConfigs: SymbolConfig[] = [
  { symbol: "BTCUSDT", enabled: true, maxPositionPct: 20 },
  { symbol: "ETHUSDT", enabled: true, maxPositionPct: 15 },
  { symbol: "SOLUSDT", enabled: true, maxPositionPct: 10 },
  { symbol: "DOGEUSDT", enabled: false, maxPositionPct: 5 },
];

// ---------- 策略实验室 ----------
export const mockLabCandidates: LabCandidate[] = [
  {
    id: "c_01",
    title: "趋势跟随 v2：ATR 动态止损倍数 2.2→2.8",
    source: "ai",
    stage: "shadow",
    shadowProgressPct: 72,
    shadowDays: 10,
    createdAt: "2026-06-23",
    promotable: true,
    metrics: [
      { k: "交易数", shadow: 34, live: 31, better: "tie" },
      { k: "胜率", shadow: "61%", live: "57%", better: "shadow" },
      { k: "净收益", shadow: "+4.8%", live: "+3.9%", better: "shadow" },
      { k: "Sharpe", shadow: 1.98, live: 1.84, better: "shadow" },
      { k: "最大回撤", shadow: "-3.1%", live: "-4.2%", better: "shadow" },
    ],
  },
  {
    id: "c_02",
    title: "突破确认：加入资金费率过滤（>0.05% 不追多）",
    source: "manual",
    stage: "shadow",
    shadowProgressPct: 31,
    shadowDays: 4,
    createdAt: "2026-06-29",
    promotable: false,
    blockReason: "影子期进度 31% < 60%，继续观察",
    metrics: [
      { k: "交易数", shadow: 9, live: 12, better: "tie" },
      { k: "胜率", shadow: "56%", live: "48%", better: "shadow" },
      { k: "净收益", shadow: "+0.9%", live: "+1.2%", better: "live" },
      { k: "Sharpe", shadow: 1.44, live: 1.51, better: "live" },
      { k: "最大回撤", shadow: "-1.8%", live: "-1.6%", better: "live" },
    ],
  },
];

export const mockLabHistory: LabHistoryItem[] = [
  { ts: "2026-06-18", kind: "promote", title: "趋势跟随 v1.3 → LIVE", note: "影子期 14d 全指标优于基线" },
  { ts: "2026-06-05", kind: "rollback", title: "区间反转 v0.9 灰度回滚", note: "灰度期回撤 -2.4% 触发自动回滚" },
  { ts: "2026-05-21", kind: "retire", title: "网格试验 v0.2 归档", note: "与现货做多定位不符" },
];

// ---------- 审计 / 报告 ----------
export const mockAuditLogs: AuditLog[] = [
  { id: "a_1", ts: "14:23:08", actor: "system", action: "guard.pass", detail: "决策 d_7f3a9b 守卫通过 8/8", system: true },
  { id: "a_2", ts: "13:02:11", actor: "danerlt", action: "config.update", detail: "修改 LLM 温度 0.3 → 0.25", system: false },
  { id: "a_3", ts: "12:30:12", actor: "system", action: "guard.reject", detail: "决策 d_7f3a99 RR<1.5 拒绝", system: true },
  { id: "a_4", ts: "09:00:00", actor: "system", action: "report.generate", detail: "生成 2026-07-02 日报", system: true },
];

export const mockReports: DailyReport[] = [
  {
    id: "r_1",
    date: "2026-07-02",
    narrative:
      "今日执行 7 笔决策，3 笔开仓 2 笔止盈 2 笔观望。BTC 维持 trending_up，趋势跟随策略贡献主要盈利 +$1,248。守卫拦截 1 笔 RR 不达标决策。日亏损 -0.48%，距熔断阈值有充足空间。",
    pnl: 1248.05,
    trades: 7,
  },
];

// ---------- 用户 / RBAC ----------
export const mockUsers: User[] = [
  { id: "u_1", name: "Daner Li", email: "danerlt001@gmail.com", role: "owner", status: "active", twoFa: true, lastActive: "刚刚" },
  { id: "u_2", name: "Ops Bot", email: "ops@alphapilot.local", role: "admin", status: "active", twoFa: true, lastActive: "2h 前" },
  { id: "u_3", name: "王观察", email: "viewer@example.com", role: "viewer", status: "pending", twoFa: false, lastActive: "—" },
];

// 与后端 src/services/system/permissions.py PERMISSION_MATRIX 严格同构（key 一致）
export const mockPermissions: PermissionRow[] = [
  { key: "trade.view", label: "查看持仓与行情", group: "trade", granted: { owner: true, admin: true, trader: true, viewer: true } },
  { key: "trade.manual_order", label: "手动下单 / 平仓", group: "trade", granted: { owner: true, admin: true, trader: true, viewer: false } },
  { key: "trade.engine_toggle", label: "启停自动交易", group: "trade", granted: { owner: true, admin: true, trader: true, viewer: false } },
  { key: "risk.edit_hard_limits", label: "修改硬风控阈值", group: "trade", granted: { owner: true, admin: true, trader: false, viewer: false } },
  { key: "lab.view", label: "查看策略与实验室", group: "strategy", granted: { owner: true, admin: true, trader: true, viewer: true } },
  { key: "lab.submit_candidate", label: "提交策略候选", group: "strategy", granted: { owner: true, admin: true, trader: true, viewer: false } },
  { key: "lab.approve_promote", label: "批准灰度 / 上线", group: "strategy", granted: { owner: true, admin: true, trader: false, viewer: false } },
  { key: "system.exchange_config", label: "交易所 API 配置", group: "system", granted: { owner: true, admin: true, trader: false, viewer: false } },
  { key: "system.llm_config", label: "LLM 模型配置", group: "system", granted: { owner: true, admin: true, trader: false, viewer: false } },
  { key: "system.user_management", label: "用户与权限管理", group: "system", granted: { owner: true, admin: true, trader: false, viewer: false } },
  { key: "system.emergency_stop", label: "紧急停止引擎", group: "system", granted: { owner: true, admin: true, trader: true, viewer: false } },
];
