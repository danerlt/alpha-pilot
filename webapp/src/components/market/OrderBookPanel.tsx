/** 盘口 / 逐笔成交 —— 对齐设计稿 market.jsx OrderBook / RecentTrades */
import { ArrowDown, ArrowUp } from "lucide-react";
import type { OrderBook, RecentTrade } from "@/api/types";
import { fmt } from "@/lib/format";

function priceDigits(p: number) {
  return p > 1000 ? 1 : 2;
}

export function OrderBookView({
  book,
  price,
  changePct,
}: {
  book: OrderBook;
  price: number;
  changePct: number;
}) {
  const maxSz = Math.max(
    ...book.asks.map((a) => a.qty),
    ...book.bids.map((b) => b.qty),
    0.001,
  );
  const d = priceDigits(price);
  const Row = ({ p, qty, side }: { p: number; qty: number; side: "ask" | "bid" }) => (
    <div className="relative flex justify-between px-2.5 py-[3px] font-mono text-xs">
      <div
        className={`absolute bottom-0 right-0 top-0 ${side === "ask" ? "bg-rose-soft" : "bg-mint-soft"}`}
        style={{ width: `${(qty / maxSz) * 100}%` }}
      />
      <span className={`relative ${side === "ask" ? "text-rose" : "text-mint"}`}>
        {fmt(p, d)}
      </span>
      <span className="relative text-fg-3">{qty.toFixed(3)}</span>
    </div>
  );
  const up = changePct >= 0;
  return (
    <div>
      <div className="flex justify-between px-2.5 pb-1.5 text-[9.5px] uppercase tracking-[.06em] text-fg-4">
        <span>价格</span>
        <span>数量</span>
      </div>
      {[...book.asks].reverse().slice(0, 8).map((a) => (
        <Row key={a.price} p={a.price} qty={a.qty} side="ask" />
      ))}
      <div
        className={`my-[3px] flex items-center gap-2 border-b border-t border-line-soft px-2.5 py-[7px] font-mono text-sm font-bold ${up ? "text-mint" : "text-rose"}`}
      >
        {fmt(price, d)}
        {up ? <ArrowUp size={13} /> : <ArrowDown size={13} />}
      </div>
      {book.bids.slice(0, 8).map((b) => (
        <Row key={b.price} p={b.price} qty={b.qty} side="bid" />
      ))}
    </div>
  );
}

export function RecentTradesView({
  trades,
  price,
}: {
  trades: RecentTrade[];
  price: number;
}) {
  const d = priceDigits(price);
  return (
    <div>
      <div className="flex justify-between px-2.5 pb-1.5 text-[9.5px] uppercase tracking-[.06em] text-fg-4">
        <span>价格</span>
        <span>数量</span>
        <span>时间</span>
      </div>
      {trades.slice(0, 14).map((t, i) => (
        <div key={i} className="flex justify-between px-2.5 py-[3px] font-mono text-xs">
          <span className={t.side === "BUY" ? "text-mint" : "text-rose"}>
            {fmt(t.price, d)}
          </span>
          <span className="text-fg-2">{t.qty.toFixed(3)}</span>
          <span className="text-fg-4">{t.ts}</span>
        </div>
      ))}
    </div>
  );
}
