/**
 * 领域类型 —— 基线来自仓库现有 API（positions/trades/decisions/...），
 * 差距接口契约见 AlphaPilot Design System/handoff/03_API_差距与新增接口.md。
 * mock 与真实后端共用同一套类型，后端就绪后切 VITE_API_BASE_URL 即可。
 */

// ---------- 全局 / 风控 ----------
export type Regime = "trending_up" | "trending_down" | "ranging" | "chaotic";
export type RiskStateLevel = "OK" | "WARN" | "HALTED";

export interface RiskState {
  state: RiskStateLevel;
  dayLossPct: number;
  positionsPct: number;
  regime: Regime;
}

// ---------- AI 决策 ----------
export type DecisionAction = "OPEN_LONG" | "CLOSE_LONG" | "HOLD";
export type GuardVerdict = "PASS" | "REJECT" | "DEGRADE";

export interface DecisionFeature {
  k: string;
  v: string;
  ok: boolean;
}

export interface GuardCheck {
  k: string;
  ok: boolean;
  note: string;
}

export interface Decision {
  id: string;
  ts: string; // HH:mm:ss（mock）/ ISO（真后端）
  symbol: string;
  timeframe: string;
  action: DecisionAction;
  confidence: number;
  strategy: string;
  guard: GuardVerdict;
  reason: string;
  entry?: number;
  sl?: number;
  tp?: number;
  sizePct?: string;
  features?: DecisionFeature[];
  guards?: GuardCheck[];
}

/** WS decision.progress 事件（handoff/03 §3.3） */
export type DecisionStage =
  | "snapshot"
  | "reasoning"
  | "guard"
  | "verdict"
  | "execute";

export interface DecisionProgressEvent {
  decisionId: string;
  stage: DecisionStage;
  status: "start" | "done" | "fail";
  ts: string;
  payload?: Record<string, unknown>;
}

// ---------- 持仓 / 订单 / 交易 ----------
export interface Position {
  id: string;
  symbol: string;
  side: "LONG";
  qty: number;
  entry: number;
  mark: number;
  pnl: number;
  pnlPct: number;
  marginPct: number;
  sl: number;
  tp: number;
  age: string;
  strategy: string;
}

export type OrderStatus = "FILLED" | "WORKING" | "CANCELED";
export type OrderType = "MARKET" | "LIMIT" | "STOP" | "TAKE_PROFIT";

export interface Order {
  id: string;
  ts: string;
  symbol: string;
  side: "BUY" | "SELL";
  type: OrderType;
  qty: number;
  price: number;
  status: OrderStatus;
}

export interface Trade {
  id: string;
  ts: string;
  symbol: string;
  action: "OPEN_LONG" | "CLOSE_LONG";
  qty: number;
  entry: number;
  exit?: number;
  pnl?: number;
  pnlPct?: number;
  exitType?: "TP" | "SL" | "MANUAL" | "AI";
  strategy: string;
}

// ---------- 守卫预检（handoff/03 §3.2） ----------
export interface PrecheckItem {
  check: string;
  pass: boolean;
  note: string;
}

export interface PrecheckResult {
  verdict: GuardVerdict;
  items: PrecheckItem[];
}

export interface OrderTicketPayload {
  symbol: string;
  side: "BUY" | "SELL";
  type: "MARKET" | "LIMIT" | "STOP";
  qty: number;
  price?: number;
  sl?: number;
  tp?: number;
  reduceOnly: boolean;
}

// ---------- 账户 ----------
export interface AccountSnapshot {
  ts: string;
  equity: number;
}

export interface AccountOverview {
  equity: number;
  equityChange: number;
  equityChangePct: number;
  todayPnl: number;
  todayPnlPct: number;
  weekPnl: number;
  weekPnlPct: number;
  mtdPnl: number;
  mtdPnlPct: number;
  tradesToday: number;
  winRate: number;
  sharpe: number;
  maxDD: number;
  avgHold: string;
}

// ---------- 行情（handoff/03 §3.1） ----------
export interface MarketSymbol {
  symbol: string;
  price: number;
  changePct24h: number;
  volume24h: number;
  hasPosition: boolean;
  regime: Regime;
}

export interface Kline {
  t: number; // epoch ms
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}

export interface Ticker {
  symbol: string;
  high24h: number;
  low24h: number;
  volume24h: number;
  markPrice: number;
  indexPrice: number;
  fundingRate: number;
  openInterest: number;
  nextFundingIn: string;
}

export interface OrderBookLevel {
  price: number;
  qty: number;
}

export interface OrderBook {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

export interface RecentTrade {
  ts: string;
  price: number;
  qty: number;
  side: "BUY" | "SELL";
}

// ---------- 事件流 ----------
export type EventKind =
  | "ai"
  | "guard"
  | "fill"
  | "order"
  | "breaker"
  | "system";

export type EventTone = "mint" | "rose" | "amber" | "violet" | "cyan" | "fg";

export interface EventItem {
  id: string;
  ts: string;
  kind: EventKind;
  msg: string;
  tone: EventTone;
}

// ---------- 绩效（handoff/03 §3.8） ----------
export interface PerformanceSummary {
  netReturnPct: number;
  hodlBtcReturnPct: number;
  sharpe: number;
  sortino: number;
  maxDD: number;
  winRate: number;
  profitFactor: number;
  curve: { ts: string; strategy: number; hodl: number }[];
}

export interface MonthlyPnl {
  month: string;
  pnl: number;
}

export type AttributionDim = "symbol" | "strategy" | "trigger";

export interface AttributionRow {
  key: string;
  trades: number;
  pnl: number;
  winRate: number;
}

// ---------- 策略与风控 ----------
export interface StrategyCard {
  id: string;
  name: string;
  enabled: boolean;
  regimes: Regime[];
  desc: string;
}

export interface HardLimit {
  key: string;
  label: string;
  value: string;
  desc: string;
}

export interface SymbolConfig {
  symbol: string;
  enabled: boolean;
  maxPositionPct: number;
}

// ---------- 策略实验室（handoff/03 §3.5） ----------
export type LabStage = "queued" | "shadow" | "canary" | "live" | "retired";

export interface LabMetricPair {
  k: string;
  shadow: number | string;
  live: number | string;
  better: "shadow" | "live" | "tie";
}

export interface LabCandidate {
  id: string;
  title: string;
  source: "ai" | "manual";
  stage: LabStage;
  shadowProgressPct: number;
  shadowDays: number;
  metrics: LabMetricPair[];
  createdAt: string;
  promotable: boolean;
  blockReason?: string;
}

export interface LabHistoryItem {
  ts: string;
  kind: "promote" | "rollback" | "retire";
  title: string;
  note?: string;
}

// ---------- 审计 / 报告 ----------
export interface AuditLog {
  id: string;
  ts: string;
  actor: string;
  action: string;
  detail: string;
  system: boolean;
}

export interface DailyReport {
  id: string;
  date: string;
  narrative: string;
  pnl: number;
  trades: number;
}

// ---------- 认证 / 用户 / RBAC（handoff/03 §3.7） ----------
export type Role = "owner" | "admin" | "trader" | "viewer";
export type UserStatus = "active" | "pending" | "disabled";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  status: UserStatus;
  twoFa: boolean;
  lastActive: string;
}

export interface PermissionRow {
  key: string;
  label: string;
  group: "trade" | "strategy" | "system";
  granted: Record<Role, boolean>;
}

// ---------- 设置（handoff/03 §3.6） ----------
export interface ExchangeSettings {
  exchange: "binance" | "hyperliquid";
  network: "testnet" | "mainnet";
  apiKeyMasked: string;
  permissions: { read: boolean; trade: boolean; withdraw: boolean };
}

export interface LlmSettings {
  provider: "deepseek" | "openai" | "anthropic" | "custom";
  model: string;
  baseUrl: string;
  apiKeyMasked: string;
  temperature: number;
  maxTokens: number;
  timeoutSec: number;
  agents: { decision: string; signal: string; review: string };
}

export interface NotificationSettings {
  telegram: boolean;
  discord: boolean;
  events: { key: string; label: string; critical: boolean; on: boolean }[];
}

// ---------- Pilot AI 对话（handoff/03 §3.4） ----------
export interface ChatToolCall {
  name: string;
  status: "running" | "done";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  tools?: ChatToolCall[];
  pendingAction?: { id: string; label: string };
}
