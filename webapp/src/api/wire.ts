/**
 * Wire 适配层 —— 真实后端契约（OpenAPI 生成，snake_case）→ 前端领域类型。
 * fromWire*：services 使用（唯一路径，mock 与真实同构）；
 * toWire*：仅 MSW handlers / 测试构造 wire 响应用。
 * 字段缺口见 docs/webapp联调-后端待办.md。
 */
import type { components } from "./generated/schema";
import type {
  AccountOverview,
  AttributionRow,
  AuditLog,
  DailyReport,
  Decision,
  ExchangeSettings,
  ExchangeTestResult,
  GuardCheck,
  GuardVerdict,
  HardLimit,
  Kline,
  LabCandidate,
  LabHistoryItem,
  LabStage,
  LlmSettings,
  LlmTestResult,
  NotificationSettings,
  MarketSymbol,
  MonthlyPnl,
  Order,
  PerformanceSummary,
  PermissionRow,
  Position,
  PrecheckResult,
  Regime,
  RiskState,
  Ticker,
  Trade,
  User,
} from "./types";

type S = components["schemas"];
export type WireRiskState = S["RiskStateOut"];
export type WireAccount = S["AccountSnapshotRead"];
export type WirePosition = S["PositionRead"];
export type WireDecision = S["DecisionRead"];
export type WireDecisionDetail = S["DecisionDetailOut"];
export type WireMarketSymbol = S["MarketSymbolRead"];
export type WireKline = S["KlineRead"];
export type WireTicker = S["TickerOut"];
export type WirePrecheck = S["PrecheckOut"];
export type WireUser = S["UserRead"];
export type WireLogin = S["LoginOut"];
export type WireRoles = S["RolesOut"];
export type WireTrade = S["TradeRead"];
export type WireOrder = S["OrderListItemRead"];
export type WireLabCandidate = S["LabCandidateRead"];
export type WireLabHistory = S["LabHistoryItemRead"];
export type WireCatchup = S["CatchupOut"];
export type WireRiskLimits = S["RiskLimitsOut"];
export type WirePerfSummary = S["PerformanceSummaryOut"];
export type WireMonthlyPnl = S["MonthlyPnlRead"];
export type WireAttribution = S["AttributionBucketRead"];

const REGIMES: Regime[] = ["trending_up", "trending_down", "ranging", "chaotic"];

function asRegime(v: string | null | undefined): Regime {
  return REGIMES.includes(v as Regime) ? (v as Regime) : "ranging";
}

function timePart(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toTimeString().slice(0, 8);
}

function ageFrom(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(ms) || ms < 0) return "—";
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function countdown(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ms = new Date(iso).getTime() - Date.now();
  if (Number.isNaN(ms) || ms <= 0) return "—";
  const h = String(Math.floor(ms / 3_600_000)).padStart(2, "0");
  const m = String(Math.floor((ms % 3_600_000) / 60_000)).padStart(2, "0");
  const s = String(Math.floor((ms % 60_000) / 1000)).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

// ---------- 风控 / 账户 ----------
export function fromWireRiskState(w: WireRiskState): RiskState {
  return {
    state: w.state,
    dayLossPct: w.day_loss_pct,
    positionsPct: w.positions_pct,
    regime: asRegime(w.regime),
  };
}

/** 账户统计类字段（周/月/Sharpe/胜率等）后端 P6 绩效期才有，先归零展示 */
export function fromWireAccount(w: WireAccount): AccountOverview {
  return {
    equity: w.total_balance_usdt ?? 0,
    equityChange: w.daily_pnl ?? 0,
    equityChangePct: w.daily_pnl_pct ?? 0,
    todayPnl: w.daily_pnl ?? 0,
    todayPnlPct: w.daily_pnl_pct ?? 0,
    weekPnl: 0,
    weekPnlPct: 0,
    mtdPnl: 0,
    mtdPnlPct: 0,
    tradesToday: 0,
    winRate: 0,
    sharpe: 0,
    maxDD: 0,
    avgHold: "—",
  };
}

// ---------- 持仓 / 交易 / 订单 ----------
export function fromWirePosition(w: WirePosition): Position {
  return {
    id: String(w.id),
    symbol: w.symbol,
    side: "LONG",
    qty: w.quantity,
    entry: w.entry_price,
    mark: w.current_price ?? w.entry_price,
    pnl: w.unrealized_pnl ?? 0,
    pnlPct: w.unrealized_pnl_pct ?? 0,
    marginPct: w.position_pct ?? 0,
    sl: w.stop_loss ?? 0,
    tp: w.take_profit ?? 0,
    age: ageFrom(w.opened_at),
    strategy: w.strategy_mode ?? "—",
  };
}

const ORDER_TYPE_MAP: Record<string, Order["type"]> = {
  MARKET: "MARKET",
  LIMIT: "LIMIT",
  STOP: "STOP",
  STOP_MARKET: "STOP",
  STOP_LOSS: "STOP",
  TAKE_PROFIT: "TAKE_PROFIT",
  TAKE_PROFIT_MARKET: "TAKE_PROFIT",
};

export function fromWireOrder(w: WireOrder): Order {
  const t = (w.order_type ?? "MARKET").toUpperCase();
  const status = (w.status ?? "").toUpperCase();
  return {
    id: String(w.id),
    ts: timePart(w.submitted_at),
    symbol: w.symbol,
    side: w.side === "SELL" ? "SELL" : "BUY",
    type: ORDER_TYPE_MAP[t] ?? "MARKET",
    qty: w.quantity ?? 0,
    price: w.avg_fill_price ?? w.price ?? 0,
    status:
      status === "FILLED"
        ? "FILLED"
        : status === "CANCELED" || status === "CANCELLED"
          ? "CANCELED"
          : "WORKING",
  };
}

export function fromWireTrade(w: WireTrade): Trade {
  const reason = (w.exit_reason ?? "").toUpperCase();
  return {
    id: String(w.id),
    ts: timePart(w.closed_at),
    symbol: w.symbol,
    action: "CLOSE_LONG",
    qty: w.quantity,
    entry: w.entry_price,
    exit: w.exit_price,
    pnl: w.pnl,
    pnlPct: w.pnl_pct,
    exitType: reason.includes("TAKE") || reason === "TP"
      ? "TP"
      : reason.includes("STOP") || reason === "SL"
        ? "SL"
        : reason.includes("MANUAL")
          ? "MANUAL"
          : "AI",
    strategy: w.strategy_mode ?? "—",
  };
}

// ---------- AI 决策 ----------
/** 后端 reasoning 为分段列表，前端展示拼接 */
function joinReasoning(r: unknown): string {
  if (Array.isArray(r)) return r.map(String).join(" ");
  return r == null ? "" : String(r);
}

const VERDICTS: GuardVerdict[] = ["PASS", "REJECT", "DEGRADE"];

function asVerdict(v: string | null | undefined, fallback: GuardVerdict): GuardVerdict {
  const up = (v ?? "").toUpperCase() as GuardVerdict;
  return VERDICTS.includes(up) ? up : fallback;
}

export function fromWireDecision(w: WireDecision): Decision {
  return {
    id: String(w.id),
    ts: timePart(w.decided_at),
    symbol: w.symbol,
    timeframe: w.timeframe,
    action: w.action as Decision["action"],
    confidence: w.confidence ?? 0,
    strategy: w.strategy_mode ?? "—",
    guard: asVerdict(w.guard_verdict, w.is_fallback ? "DEGRADE" : "PASS"),
    reason: joinReasoning(w.reasoning),
    entry: w.entry_price ?? undefined,
    sl: w.stop_loss ?? undefined,
    tp: w.take_profit ?? undefined,
    sizePct:
      w.position_size_pct != null ? `${w.position_size_pct}%` : undefined,
  };
}

export function fromWireDecisionDetail(w: WireDecisionDetail): Decision {
  const features = Object.entries(
    (w.features ?? {}) as Record<string, unknown>,
  ).map(([k, v]) => ({ k, v: String(v), ok: true }));
  const guards: GuardCheck[] = (w.guard_events ?? []).map((g) => ({
    k: g.event_type,
    ok: g.resolved ?? false,
    note: g.description ?? "",
  }));
  return {
    id: String(w.id),
    ts: timePart(w.decided_at),
    symbol: w.symbol,
    timeframe: w.timeframe,
    action: w.action as Decision["action"],
    confidence: w.confidence ?? 0,
    strategy: w.strategy_mode ?? "—",
    guard: w.is_fallback ? "DEGRADE" : guards.some((g) => !g.ok) ? "REJECT" : "PASS",
    reason: joinReasoning(w.reasoning),
    entry: w.entry_price ?? undefined,
    sl: w.stop_loss ?? undefined,
    tp: w.take_profit ?? undefined,
    sizePct: w.position_size_pct != null ? `${w.position_size_pct}%` : undefined,
    features: features.length > 0 ? features : undefined,
    guards: guards.length > 0 ? guards : undefined,
  };
}

// ---------- 行情 ----------
export function fromWireMarketSymbol(w: WireMarketSymbol): MarketSymbol {
  return {
    symbol: w.symbol,
    price: w.last_price ?? 0,
    changePct24h: w.price_change_pct ?? 0,
    volume24h: w.quote_volume_24h ?? 0,
    hasPosition: w.has_position ?? false,
    regime: asRegime(w.regime),
  };
}

export function fromWireKline(w: WireKline): Kline {
  return {
    t: new Date(w.open_time).getTime(),
    o: w.open,
    h: w.high,
    l: w.low,
    c: w.close,
    v: w.volume,
  };
}

export function fromWireTicker(w: WireTicker): Ticker {
  return {
    symbol: w.symbol,
    high24h: w.high_24h ?? 0,
    low24h: w.low_24h ?? 0,
    volume24h: w.volume_24h ?? 0,
    markPrice: w.mark_price ?? w.last_price,
    indexPrice: w.index_price ?? w.last_price,
    fundingRate: w.funding_rate ?? 0,
    openInterest: w.open_interest ?? 0,
    nextFundingIn: countdown(w.next_funding_time),
  };
}

// ---------- 守卫预检 ----------
export function fromWirePrecheck(w: WirePrecheck): PrecheckResult {
  return {
    verdict: w.verdict as PrecheckResult["verdict"],
    items: (w.checks ?? []).map((c) => ({
      check: c.check,
      pass: c.pass,
      note: c.note ?? "",
      category: (c.category as PrecheckResult["items"][number]["category"]) ?? "soft",
    })),
  };
}

// ---------- 风控阈值 ----------
export function fromWireRiskLimits(w: WireRiskLimits): HardLimit[] {
  return [
    { key: "MAX_POSITION_SIZE_PCT", label: "单仓位上限", value: `${w.max_position_size_pct}%`, desc: "任一持仓占权益比例上限" },
    { key: "MAX_DAILY_LOSS_PCT", label: "日亏损熔断", value: `${w.max_daily_loss_pct}%`, desc: "当日亏损超过即熔断，全天禁止开仓" },
    { key: "MAX_CONSECUTIVE_LOSSES", label: "连续亏损熔断", value: `${w.max_consecutive_losses} 笔`, desc: "连续亏损达到阈值触发熔断" },
    { key: "MAX_SINGLE_RISK_PCT", label: "单笔风险上限", value: `${w.max_single_risk_pct}%`, desc: "单笔交易最大可亏损占权益比例" },
    { key: "MIN_RR_RATIO", label: "最小盈亏比", value: `${w.min_rr_ratio}`, desc: "开仓要求的最低风险收益比" },
    { key: "SL_ATR_MULT", label: "止损 ATR 倍数", value: `${w.sl_atr_min_mult}–${w.sl_atr_max_mult}x`, desc: "止损距离相对 ATR 的允许区间" },
  ];
}

// ---------- 绩效 ----------
function humanizeSeconds(s: number | null | undefined): string {
  if (!s || s <= 0) return "—";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

interface CurvePoint {
  ts?: unknown;
  equity?: unknown;
  hodl?: unknown;
}

/** 后端 curve 为绝对权益（HODL 已归一到同起点），前端换算为相对首点的收益率 % */
export function fromWirePerfSummary(w: WirePerfSummary): PerformanceSummary {
  const raw = (w.curve ?? []) as CurvePoint[];
  const first = raw.find((p) => typeof p.equity === "number");
  const base = typeof first?.equity === "number" ? first.equity : 0;
  const curve = base
    ? raw
        .filter((p) => typeof p.equity === "number")
        .map((p) => ({
          ts: String(p.ts ?? ""),
          strategy: ((p.equity as number) / base - 1) * 100,
          hodl:
            typeof p.hodl === "number" ? (p.hodl / base - 1) * 100 : 0,
        }))
    : [];
  return {
    netReturnPct: w.net_return_pct ?? 0,
    hodlBtcReturnPct: w.hodl_return_pct ?? 0,
    sharpe: w.sharpe ?? 0,
    sortino: w.sortino ?? 0,
    maxDD: w.max_drawdown_pct ?? 0,
    winRate: w.win_rate ?? 0,
    profitFactor: w.profit_factor ?? 0,
    trades: w.trades,
    netPnl: w.net_pnl,
    todayTrades: w.today_trades,
    avgHold: humanizeSeconds(w.avg_holding_seconds),
    weekPnl: w.week_pnl,
    monthPnl: w.month_pnl,
    curve,
  };
}

export function fromWireMonthly(w: WireMonthlyPnl): MonthlyPnl {
  return { month: w.month, pnl: w.pnl, trades: w.trades };
}

export function fromWireAttribution(w: WireAttribution): AttributionRow {
  return {
    key: w.key,
    trades: w.trades,
    pnl: w.net_pnl,
    winRate: w.win_rate ?? 0,
  };
}

// ---------- 策略实验室 ----------
interface LabSideMetrics {
  decisions?: number;
  trades?: number;
  simulated_pnl_pct?: number | null;
  net_pnl_pct?: number | null;
  win_rate?: number | null;
}

const LAB_STAGES: LabStage[] = ["queued", "shadow", "canary", "live", "retired"];

export function fromWireLabCandidate(w: WireLabCandidate): LabCandidate {
  const m = (w.metrics ?? {}) as { shadow?: LabSideMetrics; live?: LabSideMetrics };
  const s = m.shadow ?? {};
  const l = m.live ?? {};
  const pct = (v: number | null | undefined) =>
    v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
  const wr = (v: number | null | undefined) =>
    v == null ? "—" : `${(v * 100).toFixed(0)}%`;
  const better = (
    a: number | null | undefined,
    b: number | null | undefined,
  ): "shadow" | "live" | "tie" =>
    a == null || b == null ? "tie" : a > b ? "shadow" : a < b ? "live" : "tie";
  const progress = w.shadow_progress ?? 0;
  const target = w.shadow_days_target ?? 14;
  return {
    id: String(w.id),
    title: w.name,
    source: w.source === "manual" ? "manual" : "ai",
    stage: LAB_STAGES.includes(w.stage as LabStage)
      ? (w.stage as LabStage)
      : "queued",
    shadowProgressPct: Math.round(progress * 100),
    shadowDays: Math.round(progress * target),
    metrics: [
      { k: "决策数(影)/交易数(线)", shadow: s.decisions ?? 0, live: l.trades ?? 0, better: "tie" },
      { k: "净收益", shadow: pct(s.simulated_pnl_pct), live: pct(l.net_pnl_pct), better: better(s.simulated_pnl_pct, l.net_pnl_pct) },
      { k: "胜率", shadow: wr(s.win_rate), live: wr(l.win_rate), better: better(s.win_rate, l.win_rate) },
    ],
    createdAt: (w.created_at ?? "").slice(0, 10),
    promotable: w.promote_eligible,
    blockReason: w.promote_blocked_reason ?? undefined,
  };
}

export function fromWireLabHistory(w: WireLabHistory): LabHistoryItem {
  const a = (w.action ?? "").toLowerCase();
  return {
    ts: (w.at ?? "").slice(0, 10),
    kind: a.includes("promote") ? "promote" : a.includes("rollback") ? "rollback" : "retire",
    title: w.candidate_name ?? `候选 #${w.candidate_id}`,
    note: [w.reason, w.operator].filter(Boolean).join(" · ") || undefined,
  };
}

// ---------- 审计 / 日报（无 response_model 的端点，手写 wire 接口） ----------
export interface WireAuditLog {
  id: number;
  actor: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | number | null;
  created_at?: string | null;
}

export function fromWireAuditLog(w: WireAuditLog): AuditLog {
  const res = [w.resource_type, w.resource_id].filter(Boolean).join(" #");
  return {
    id: String(w.id),
    ts: timePart(w.created_at),
    actor: w.actor ?? "system",
    action: w.action,
    detail: res ? `${w.action} · ${res}` : w.action,
    system: w.actor == null,
  };
}

export interface WireReport {
  id: number;
  report_date: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate?: number | null;
  total_pnl: number;
  total_pnl_pct: number;
  max_drawdown?: number | null;
  risk_events_count?: number | null;
}

export function fromWireReport(w: WireReport): DailyReport {
  const wr = w.win_rate != null ? `${(w.win_rate * 100).toFixed(0)}%` : "—";
  return {
    id: String(w.id),
    date: w.report_date,
    // 后端日报暂无 LLM 叙述字段，由统计合成（待 AI 日报叙述落地后替换）
    narrative:
      `本日执行 ${w.total_trades} 笔交易（盈 ${w.winning_trades} / 亏 ${w.losing_trades}，胜率 ${wr}），` +
      `净盈亏 ${w.total_pnl >= 0 ? "+" : ""}${w.total_pnl.toFixed(2)} USDT（${w.total_pnl_pct >= 0 ? "+" : ""}${w.total_pnl_pct.toFixed(2)}%）。` +
      (w.max_drawdown != null ? `当日最大回撤 ${w.max_drawdown.toFixed(2)}%。` : "") +
      (w.risk_events_count ? `风控事件 ${w.risk_events_count} 次。` : "风控无异常。"),
    pnl: w.total_pnl,
    trades: w.total_trades,
  };
}

// ---------- Agent（handoff 3.4） ----------
export interface WireAgentHistoryItem {
  invocation_id: number;
  message: string;
  answer: string;
  tools?: string[] | null;
  pending_action_id?: number | null;
  occurred_at?: string | null;
}

// ---------- 设置 ----------
export type WireExchangeSettings = S["ExchangeSettingsOut"];
export type WireExchangeTest = S["ExchangeTestOut"];
export type WireLlmSettings = S["LlmSettingsOut"];
export type WireLlmTest = S["LlmTestOut"];
export type WireNotificationSettings = S["NotificationSettingsOut"];

export function fromWireExchangeSettings(
  w: WireExchangeSettings,
): ExchangeSettings {
  const net = (n?: { api_key_masked?: string | null; has_secret?: boolean }) => ({
    apiKeyMasked: n?.api_key_masked ?? null,
    hasSecret: n?.has_secret ?? false,
  });
  return {
    network: w.network === "mainnet" ? "mainnet" : "testnet",
    apiKeyMasked: w.api_key_masked ?? null,
    hasSecret: w.has_secret ?? false,
    mainnet: net(w.mainnet),
    testnet: net(w.testnet),
  };
}

export function fromWireExchangeTest(w: WireExchangeTest): ExchangeTestResult {
  const p = (w.permissions ?? null) as
    | { read?: boolean; trade?: boolean; withdraw?: boolean }
    | null;
  return {
    ok: w.ok,
    permissions: p
      ? {
          read: p.read ?? false,
          trade: p.trade ?? false,
          withdraw: p.withdraw ?? false,
        }
      : null,
    warning: w.warning ?? null,
    error: w.error ?? null,
  };
}

export function fromWireLlmSettings(w: WireLlmSettings): LlmSettings {
  return {
    model: w.model ?? "",
    baseUrl: w.base_url ?? "",
    apiKeyMasked: w.api_key_masked ?? null,
    temperature: w.temperature ?? 0.3,
    timeoutSeconds: w.timeout_seconds ?? 30,
    agentModels: w.agent_models ?? {},
  };
}

export function fromWireLlmTest(w: WireLlmTest): LlmTestResult {
  return { ok: w.ok, latencyMs: w.latency_ms ?? null, error: w.error ?? null };
}

export function fromWireNotificationSettings(
  w: WireNotificationSettings,
): NotificationSettings {
  return {
    channels: w.channels ?? {},
    subscriptions: w.subscriptions ?? {},
    telegramBotTokenMasked: w.telegram_bot_token_masked ?? null,
    telegramChatId: w.telegram_chat_id ?? null,
    minSeverity: w.min_severity ?? null,
  };
}

// ---------- 用户 / 权限 ----------
const ROLE_ALIAS: Record<string, User["role"]> = {
  owner: "owner",
  admin: "admin",
  trader: "trader",
  viewer: "viewer",
  user: "trader", // 后端过渡别名（permissions.py role_aliases）
};

export function fromWireUser(w: WireUser): User {
  return {
    id: String(w.id),
    name: w.username,
    email: w.email ?? "",
    role: ROLE_ALIAS[w.role] ?? "viewer",
    status: (w.status as User["status"]) ?? "active",
    twoFa: w.two_fa_enabled ?? false,
    lastActive: "—",
  };
}

const GROUP_KEY: Record<string, PermissionRow["group"]> = {
  交易: "trade",
  策略: "strategy",
  系统: "system",
  trade: "trade",
  strategy: "strategy",
  system: "system",
};

export function fromWireRoles(w: WireRoles): PermissionRow[] {
  return w.matrix.flatMap((g) =>
    g.items.map((it) => ({
      key: it.key,
      label: it.label,
      group: GROUP_KEY[g.group] ?? "system",
      granted: {
        owner: it.owner,
        admin: it.admin,
        trader: it.trader,
        viewer: it.viewer,
      },
    })),
  );
}
