/**
 * 实时事件流 —— 统一订阅接口（handoff/03 §3.9 WS 事件面）。
 * mock 模式：本地定时器驱动（账户快照/事件流/决策周期/行情 tick + 场景模拟）；
 * 真后端：单条 WebSocket（VITE_WS_URL，或由 VITE_API_BASE_URL 推导 + /ws），
 * 消息格式 {type, payload}，断线指数退避重连，补偿走 /api/events/catchup（页面侧已接）。
 */
import { USE_MOCK } from "./client";
import type {
  AccountSnapshot,
  Decision,
  DecisionProgressEvent,
  EventItem,
  RiskState,
} from "./types";
import { mockAccount, mockRiskState } from "./mock/data";

export type Scene = "ok" | "warn" | "halted";

export interface TickerUpdate {
  symbol: string;
  price: number;
  changePct24h: number;
}

export interface StreamEvents {
  "risk.state": RiskState;
  "account.snapshot": AccountSnapshot;
  "event.append": EventItem;
  "decision.progress": DecisionProgressEvent;
  "decision.complete": Decision;
  "market.ticker": TickerUpdate;
}

export type StreamTopic = keyof StreamEvents;

interface Stream {
  subscribe<T extends StreamTopic>(
    topic: T,
    cb: (payload: StreamEvents[T]) => void,
  ): () => void;
  /** 场景模拟（仅 mock 生效）：驱动 HALTED 五件套联动演示 */
  setScene(scene: Scene): void;
  /** 本地补一条事件（仅 mock 生效，如「配置修改已确认」） */
  emitEvent(e: Omit<EventItem, "id" | "ts">): void;
}

function nowTs(): string {
  return new Date().toTimeString().slice(0, 8);
}

// ============================================================
// Mock 流
// ============================================================
class MockStream implements Stream {
  private handlers = new Map<StreamTopic, Set<(p: never) => void>>();
  private timers: ReturnType<typeof setInterval>[] = [];
  private cycleTimers: ReturnType<typeof setTimeout>[] = [];
  private subscriberCount = 0;
  private scene: Scene = "ok";
  private equity = mockAccount.equity;
  private prices: Record<string, number> = { BTCUSDT: 68863.92, ETHUSDT: 3219.92 };
  private seq = 0;
  private decisionSeq = 0;

  subscribe<T extends StreamTopic>(
    topic: T,
    cb: (payload: StreamEvents[T]) => void,
  ): () => void {
    if (!this.handlers.has(topic)) this.handlers.set(topic, new Set());
    this.handlers.get(topic)!.add(cb as (p: never) => void);
    this.subscriberCount++;
    if (this.subscriberCount === 1) this.start();
    return () => {
      this.handlers.get(topic)?.delete(cb as (p: never) => void);
      this.subscriberCount--;
      if (this.subscriberCount <= 0) this.stop();
    };
  }

  setScene(scene: Scene) {
    this.scene = scene;
    this.emit("risk.state", this.riskState());
    if (scene === "halted") {
      this.emit("event.append", this.mkEvent({
        kind: "breaker",
        msg: "熔断触发 · 日亏损达到阈值 · 新开仓已暂停",
        tone: "rose",
      }));
    } else if (scene === "ok") {
      this.emit("event.append", this.mkEvent({
        kind: "system",
        msg: "熔断已手动解除 · 引擎恢复自动交易",
        tone: "mint",
      }));
    }
  }

  emitEvent(e: Omit<EventItem, "id" | "ts">) {
    this.emit("event.append", this.mkEvent(e));
  }

  // ---------- 内部 ----------
  private riskState(): RiskState {
    if (this.scene === "halted")
      return { state: "HALTED", dayLossPct: -2.31, positionsPct: 12, regime: "chaotic" };
    if (this.scene === "warn")
      return { state: "WARN", dayLossPct: -1.62, positionsPct: 14, regime: "ranging" };
    return { ...mockRiskState };
  }

  private mkEvent(e: Omit<EventItem, "id" | "ts">): EventItem {
    return { ...e, id: `e_live_${++this.seq}`, ts: nowTs() };
  }

  private emit<T extends StreamTopic>(topic: T, payload: StreamEvents[T]) {
    this.handlers.get(topic)?.forEach((cb) => (cb as (p: StreamEvents[T]) => void)(payload));
  }

  private start() {
    // 账户快照 + 行情 tick（4s）
    this.timers.push(
      setInterval(() => {
        const drift = this.scene === "halted" ? -0.35 : 0.06;
        this.equity += (Math.random() - 0.5 + drift * 0.1) * 90;
        this.emit("account.snapshot", {
          ts: nowTs().slice(0, 5),
          equity: Math.round(this.equity * 100) / 100,
        });
        for (const sym of Object.keys(this.prices)) {
          this.prices[sym] *= 1 + (Math.random() - 0.5) * 0.0008;
          this.emit("market.ticker", {
            symbol: sym,
            price: Math.round(this.prices[sym] * 100) / 100,
            changePct24h: sym === "BTCUSDT" ? 2.14 : -0.62,
          });
        }
      }, 4000),
    );

    // 事件流追加（9s）
    const pool: Omit<EventItem, "id" | "ts">[] = [
      { kind: "ai", msg: "AI 周期扫描完成 · BTCUSDT regime trending_up", tone: "violet" },
      { kind: "guard", msg: "守卫巡检 · 8 项硬风控全部正常", tone: "mint" },
      { kind: "order", msg: "止损/止盈挂单心跳确认 · 4 单在场", tone: "fg" },
      { kind: "system", msg: "行情数据同步 · 6 交易对 K 线已更新", tone: "cyan" },
      { kind: "ai", msg: "经验库检索 · 命中 3 条相似历史案例", tone: "violet" },
    ];
    let poolIdx = 0;
    this.timers.push(
      setInterval(() => {
        this.emit("event.append", this.mkEvent(pool[poolIdx++ % pool.length]));
      }, 9000),
    );

    // 完整决策周期（50s）：progress 逐段 → complete
    this.timers.push(
      setInterval(() => this.runDecisionCycle(), 50_000),
    );
  }

  private runDecisionCycle() {
    const halted = this.scene === "halted";
    const sym = this.decisionSeq % 2 === 0 ? "BTCUSDT" : "ETHUSDT";
    const id = `d_live_${++this.decisionSeq}`;
    const stages: DecisionProgressEvent["stage"][] = [
      "snapshot", "reasoning", "guard", "verdict", "execute",
    ];
    stages.forEach((stage, i) => {
      this.cycleTimers.push(
        setTimeout(() => {
          this.emit("decision.progress", { decisionId: id, stage, status: "done", ts: nowTs() });
        }, i * 750),
      );
    });
    this.cycleTimers.push(
      setTimeout(() => {
        const conf = Math.round((0.55 + Math.random() * 0.3) * 100) / 100;
        const d: Decision = halted
          ? {
              id, ts: nowTs(), symbol: sym, timeframe: "15m",
              action: "HOLD", confidence: 0.31, strategy: "熔断保护", guard: "REJECT",
              reason: "熔断状态下守卫拒绝所有新开仓，仅允许平仓与风险管理操作。",
            }
          : {
              id, ts: nowTs(), symbol: sym, timeframe: "15m",
              action: "HOLD", confidence: conf, strategy: "趋势跟随", guard: "PASS",
              reason: `周期扫描：${sym} 维持 trending_up，但回踩未到位（EMA20 上方 0.8%），等待更优入场点，本周期保持 HOLD。`,
            };
        this.emit("decision.complete", d);
        this.emit("event.append", this.mkEvent({
          kind: "ai",
          msg: `AI ${d.action} ${sym} · 置信度 ${d.confidence.toFixed(2)}`,
          tone: "violet",
        }));
        this.emit("event.append", this.mkEvent({
          kind: "guard",
          msg: halted ? "守卫拒绝 REJECT · 熔断中" : "守卫通过 PASS · 检查 8/8",
          tone: halted ? "rose" : "mint",
        }));
      }, stages.length * 750 + 300),
    );
  }

  private stop() {
    this.subscriberCount = 0;
    this.timers.forEach(clearInterval);
    this.cycleTimers.forEach(clearTimeout);
    this.timers = [];
    this.cycleTimers = [];
  }
}

// ============================================================
// 真后端 WebSocket 流
// ============================================================
class WsStream implements Stream {
  private handlers = new Map<StreamTopic, Set<(p: never) => void>>();
  private ws: WebSocket | null = null;
  private retry = 0;
  private subscriberCount = 0;

  private url(): string {
    const explicit = import.meta.env.VITE_WS_URL as string | undefined;
    if (explicit) return explicit;
    const base = (import.meta.env.VITE_API_BASE_URL as string) ?? "";
    return base.replace(/^http/, "ws") + "/ws";
  }

  subscribe<T extends StreamTopic>(
    topic: T,
    cb: (payload: StreamEvents[T]) => void,
  ): () => void {
    if (!this.handlers.has(topic)) this.handlers.set(topic, new Set());
    this.handlers.get(topic)!.add(cb as (p: never) => void);
    this.subscriberCount++;
    if (this.subscriberCount === 1) this.connect();
    return () => {
      this.handlers.get(topic)?.delete(cb as (p: never) => void);
      this.subscriberCount--;
      if (this.subscriberCount <= 0) this.disconnect();
    };
  }

  setScene() {
    // 真后端下风控状态由服务端事件驱动，场景模拟不可用
  }

  emitEvent() {
    // 真后端下事件由服务端产生
  }

  private connect() {
    try {
      this.ws = new WebSocket(this.url());
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.ws.onopen = () => {
      this.retry = 0;
    };
    this.ws.onmessage = (ev) => {
      try {
        const { type, payload } = JSON.parse(ev.data as string) as {
          type: StreamTopic;
          payload: never;
        };
        this.handlers.get(type)?.forEach((cb) => cb(payload));
      } catch {
        // 非 JSON 心跳帧等，忽略
      }
    };
    this.ws.onclose = () => this.scheduleReconnect();
    this.ws.onerror = () => this.ws?.close();
  }

  private scheduleReconnect() {
    if (this.subscriberCount <= 0) return;
    const delay = Math.min(30_000, 1000 * 2 ** this.retry++);
    setTimeout(() => this.connect(), delay);
  }

  private disconnect() {
    this.subscriberCount = 0;
    this.ws?.close();
    this.ws = null;
  }
}

export const stream: Stream = USE_MOCK ? new MockStream() : new WsStream();
