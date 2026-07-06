/**
 * 行情流 —— 盘口/逐笔（handoff P2b `/ws/market`）。
 * 协议：ws://host/ws/market?token=<jwt>&symbol=X，一连接一 symbol；
 * 下行帧 {type: "market.ticker|market.depth|market.trades", symbol, ts, data}（不走 Response 包）。
 * mock 模式：定时器抖动生成盘口 + 逐笔。
 */
import { USE_MOCK } from "./client";
import { genOrderBook, genRecentTrades } from "./mock/data";
import { getWsToken } from "./tokenStore";
import type { OrderBook, RecentTrade } from "./types";
import { resolveWsUrl } from "@/config";

export interface MarketStreamHandlers {
  onDepth?: (book: OrderBook) => void;
  onTrade?: (t: RecentTrade) => void;
}

type DepthFrame = { bids: [number, number][]; asks: [number, number][] };
type TradeFrame = { price: number; qty: number; side: "buy" | "sell"; ts?: number };

function nowHms(ms?: number): string {
  return new Date(ms ?? Date.now()).toTimeString().slice(0, 8);
}

/** 订阅某 symbol 的盘口/逐笔；返回取消函数（换 symbol = 取消后重订） */
export function subscribeMarketStream(
  symbol: string,
  handlers: MarketStreamHandlers,
): () => void {
  if (USE_MOCK) return mockSubscribe(symbol, handlers);
  return wsSubscribe(symbol, handlers);
}

// ---------- mock ----------
function mockSubscribe(symbol: string, h: MarketStreamHandlers): () => void {
  const base = genOrderBook(symbol);
  h.onDepth?.(base);
  genRecentTrades(symbol)
    .slice(0, 14)
    .reverse()
    .forEach((t) => h.onTrade?.(t));

  const timer = setInterval(() => {
    const jitter = (v: number) => v * (1 + (Math.random() - 0.5) * 0.02);
    h.onDepth?.({
      bids: base.bids.map((l) => ({ price: l.price, qty: jitter(l.qty) })),
      asks: base.asks.map((l) => ({ price: l.price, qty: jitter(l.qty) })),
    });
    const mid = base.asks[0]?.price ?? 100;
    h.onTrade?.({
      ts: nowHms(),
      price: jitter(mid),
      qty: Math.round(Math.random() * 900) / 1000,
      side: Math.random() > 0.5 ? "BUY" : "SELL",
    });
  }, 900);
  return () => clearInterval(timer);
}

// ---------- 真后端 /ws/market ----------
function wsSubscribe(symbol: string, h: MarketStreamHandlers): () => void {
  let ws: WebSocket | null = null;
  let closed = false;
  let retry = 0;

  const url = () => {
    const base = resolveWsUrl().replace(/\/ws$/, "/ws/market");
    const params = new URLSearchParams({ symbol });
    const token = getWsToken();
    if (token) params.set("token", token);
    return `${base}?${params.toString()}`;
  };

  const connect = () => {
    if (closed) return;
    try {
      ws = new WebSocket(url());
    } catch {
      scheduleReconnect();
      return;
    }
    ws.onopen = () => {
      retry = 0;
    };
    ws.onmessage = (ev) => {
      try {
        const frame = JSON.parse(ev.data as string) as {
          type: string;
          ts?: number;
          data: unknown;
        };
        if (frame.type === "market.depth") {
          const d = frame.data as DepthFrame;
          h.onDepth?.({
            bids: (d.bids ?? []).map(([price, qty]) => ({ price, qty })),
            asks: (d.asks ?? []).map(([price, qty]) => ({ price, qty })),
          });
        } else if (frame.type === "market.trades") {
          const t = frame.data as TradeFrame;
          h.onTrade?.({
            ts: nowHms(t.ts),
            price: t.price,
            qty: t.qty,
            side: t.side === "buy" ? "BUY" : "SELL",
          });
        }
        // market.ticker 帧由行情页头部沿用 REST ticker + streamBridge，暂不消费
      } catch {
        // 忽略非 JSON 帧
      }
    };
    ws.onclose = () => scheduleReconnect();
    ws.onerror = () => ws?.close();
  };

  const scheduleReconnect = () => {
    if (closed) return;
    const delay = Math.min(15_000, 1000 * 2 ** retry++);
    setTimeout(connect, delay);
  };

  connect();
  return () => {
    closed = true;
    ws?.close();
    ws = null;
  };
}
