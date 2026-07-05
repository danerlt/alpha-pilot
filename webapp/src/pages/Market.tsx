/**
 * 行情页（handoff/02 P3）—— 自选 220px | K线主区 | 右栏 260px（下单+盘口+合约信息）。
 */
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BrainCircuit, Search } from "lucide-react";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Pill } from "@/components/ui/atoms";
import { AnimatedNumber } from "@/components/charts/AnimatedNumber";
import { KlineChart } from "@/components/market/KlineChart";
import { OrderBookView, RecentTradesView } from "@/components/market/OrderBookPanel";
import { OrderTicket } from "@/components/market/OrderTicket";
import { CoinAvatar } from "@/components/positions/PositionsTable";
import { marketApi, positionsApi } from "@/api/services";
import { stream } from "@/api/stream";
import type {
  Kline,
  MarketSymbol,
  OrderBook,
  Position,
  RecentTrade,
  Regime,
  Ticker,
} from "@/api/types";
import { fmt } from "@/lib/format";

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];

const regimeTone = (r: Regime) =>
  r === "trending_up"
    ? ("mint" as const)
    : r === "trending_down"
      ? ("rose" as const)
      : r === "chaotic"
        ? ("amber" as const)
        : ("cyan" as const);

function fmtVol(v: number) {
  return v >= 1e9 ? `$${(v / 1e9).toFixed(2)}B` : `$${(v / 1e6).toFixed(0)}M`;
}

export default function Market() {
  const [params, setParams] = useSearchParams();
  const symbol = params.get("symbol") ?? "BTCUSDT";
  const [tf, setTf] = useState("15m");
  const [obTab, setObTab] = useState<"book" | "trades">("book");
  const [symbols, setSymbols] = useState<MarketSymbol[]>([]);
  const [klines, setKlines] = useState<Kline[]>([]);
  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [book, setBook] = useState<OrderBook | null>(null);
  const [recent, setRecent] = useState<RecentTrade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);

  useEffect(() => {
    marketApi.symbols().then(setSymbols).catch(() => {});
    positionsApi.list().then(setPositions).catch(() => {});
  }, []);

  // 实时 ticker：更新自选列表价格（头部大数字随 AnimatedNumber 滚动）
  useEffect(() => {
    return stream.subscribe("market.ticker", (t) =>
      setSymbols((prev) =>
        prev.map((s) =>
          s.symbol === t.symbol
            ? { ...s, price: t.price, changePct24h: t.changePct24h }
            : s,
        ),
      ),
    );
  }, []);

  useEffect(() => {
    setKlines([]);
    marketApi.klines(symbol, tf, 64).then(setKlines).catch(() => {});
  }, [symbol, tf]);

  useEffect(() => {
    marketApi.ticker(symbol).then(setTicker).catch(() => {});
    marketApi.orderBook(symbol).then(setBook).catch(() => {});
    marketApi.recentTrades(symbol).then(setRecent).catch(() => {});
  }, [symbol]);

  const cur = symbols.find((s) => s.symbol === symbol);
  const price = cur?.price ?? 0;
  const chg = cur?.changePct24h ?? 0;
  const regime = cur?.regime ?? "ranging";
  const position = useMemo(
    () => positions.find((p) => p.symbol === symbol),
    [positions, symbol],
  );

  const setSymbol = (s: string) => setParams({ symbol: s }, { replace: true });

  return (
    <PageShell title="行情" sub="MARKET">
      <div className="grid h-full gap-4 min-[1180px]:grid-cols-[220px_minmax(0,1fr)_260px]">
        {/* 自选列表 */}
        <Card
          title="自选"
          right={<Search size={13} className="text-fg-4" />}
          className="h-fit"
          bodyClassName=""
        >
          {symbols.map((s) => {
            const up = s.changePct24h >= 0;
            const sel = s.symbol === symbol;
            return (
              <button
                key={s.symbol}
                onClick={() => setSymbol(s.symbol)}
                className={`flex w-full cursor-pointer items-center gap-2.5 border-b border-line-soft px-3.5 py-[11px] text-left ${
                  sel ? "bg-bg-3" : "hover:bg-bg-3/50"
                }`}
                style={{
                  borderLeft: `2px solid ${sel ? "var(--ap-mint)" : "transparent"}`,
                }}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[12.5px] font-semibold text-fg-1">
                      {s.symbol.replace("USDT", "")}
                    </span>
                    {s.hasPosition && (
                      <span
                        title="持仓中"
                        className="h-[5px] w-[5px] rounded-full bg-violet"
                        style={{ boxShadow: "0 0 5px var(--ap-violet)" }}
                      />
                    )}
                  </div>
                  <div className="font-mono text-micro text-fg-4">USDT 现货</div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-xs font-semibold text-fg-1">
                    {fmt(s.price, s.price > 1000 ? 0 : 2)}
                  </div>
                  <div className={`font-mono text-[10.5px] ${up ? "text-mint" : "text-rose"}`}>
                    {up ? "▲" : "▼"} {Math.abs(s.changePct24h).toFixed(2)}%
                  </div>
                </div>
              </button>
            );
          })}
        </Card>

        {/* 中列：K线 + AI 解读 */}
        <div className="flex min-w-0 flex-col gap-4">
          <Card>
            {/* 交易对头部 */}
            <div className="mb-3.5 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2.5">
                <CoinAvatar symbol={symbol} size={32} />
                <div>
                  <div className="font-mono text-[16px] font-bold text-fg-1">{symbol}</div>
                  <div className="text-[10.5px] text-fg-3">现货 · Binance</div>
                </div>
              </div>
              <div className="flex items-baseline gap-2.5">
                <AnimatedNumber
                  value={price}
                  prefix="$"
                  format={(v) => fmt(v, price > 1000 ? 2 : 3)}
                  className="text-[26px] font-bold text-fg-1"
                />
                <span
                  className={`font-mono text-sm font-semibold ${chg >= 0 ? "text-mint" : "text-rose"}`}
                >
                  {chg >= 0 ? "+" : ""}
                  {chg.toFixed(2)}%
                </span>
              </div>
              {ticker && cur && (
                <div className="ml-auto flex gap-[18px]">
                  {(
                    [
                      ["24h 高", fmt(ticker.high24h, 0)],
                      ["24h 低", fmt(ticker.low24h, 0)],
                      ["24h 量", fmtVol(cur.volume24h)],
                    ] as const
                  ).map(([l, v]) => (
                    <div key={l}>
                      <div className="text-[9.5px] uppercase tracking-[.06em] text-fg-4">{l}</div>
                      <div className="font-mono text-xs font-semibold text-fg-1">{v}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {/* 周期 + regime */}
            <div className="mb-2 flex flex-wrap items-center gap-2 gap-y-1.5">
              <div className="inline-flex rounded-sm border border-line bg-bg-3 p-[3px]">
                {TIMEFRAMES.map((t) => (
                  <button
                    key={t}
                    onClick={() => setTf(t)}
                    className={`cursor-pointer rounded-[5px] px-[11px] py-[5px] font-mono text-xs font-medium ${
                      tf === t ? "bg-bg-4 text-fg-1" : "text-fg-3"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <Pill tone={regimeTone(regime)}>AI regime · {regime}</Pill>
              {position && <Pill tone="violet">持仓中</Pill>}
              <span className="ml-auto whitespace-nowrap font-mono text-[10.5px] text-fg-4">
                含 SL/TP 标线
              </span>
            </div>
            {/* K线 */}
            <div className="-mx-[18px] -mb-4">
              <KlineChart klines={klines} position={position} />
            </div>
          </Card>

          {/* AI 解读条 */}
          <Card>
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-violet-soft">
                <BrainCircuit size={16} className="text-violet" />
              </div>
              <div className="flex-1">
                <div className="mb-1 text-[10.5px] font-bold tracking-[.08em] text-violet">
                  AI 市场解读 · {symbol}
                </div>
                <div className="text-sm leading-relaxed text-fg-2">
                  {regime === "trending_up" ? (
                    <>
                      当前判定 <b className="text-mint">trending_up</b>：EMA 多头排列，{tf}{" "}
                      级别量能温和放大。
                      {position
                        ? "持仓盈利中，止盈位上移空间充足。"
                        : "符合「趋势跟随」策略入场条件，等待回踩确认。"}
                    </>
                  ) : regime === "trending_down" ? (
                    <>
                      当前判定 <b className="text-rose">trending_down</b>：EMA 空头排列。V0.1
                      仅支持现货做多，AI 保持 <b>观望</b>。
                    </>
                  ) : regime === "chaotic" ? (
                    <>
                      当前判定 <b className="text-amber">chaotic</b>：波动率异常放大，守卫将对开仓决策执行{" "}
                      <b>DEGRADE</b> 降级。
                    </>
                  ) : (
                    <>
                      当前判定 <b className="text-cyan">ranging</b>：价格在区间内震荡，方向性不足。AI 倾向{" "}
                      <b>观望</b>，仅在突破区间边界且放量时考虑入场。
                    </>
                  )}
                </div>
                {ticker && (
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    <Pill tone="cyan">资金费率 {(ticker.fundingRate * 100).toFixed(4)}%</Pill>
                    <Pill>持仓量 {fmt(ticker.openInterest, 0)}</Pill>
                    <Pill>下次结算 {ticker.nextFundingIn}</Pill>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* 右列：下单 + 盘口/成交 + 市场信息 */}
        <div className="flex min-w-0 flex-col gap-4">
          <OrderTicket symbol={symbol} price={price} />

          <Card
            className="h-fit"
            title={
              <div className="flex gap-3">
                <button
                  onClick={() => setObTab("book")}
                  className={`cursor-pointer ${obTab === "book" ? "text-fg-1" : "text-fg-4"}`}
                >
                  盘口
                </button>
                <button
                  onClick={() => setObTab("trades")}
                  className={`cursor-pointer ${obTab === "trades" ? "text-fg-1" : "text-fg-4"}`}
                >
                  成交
                </button>
              </div>
            }
            bodyClassName="py-2"
          >
            {obTab === "book" ? (
              book && <OrderBookView book={book} price={price} changePct={chg} />
            ) : (
              <RecentTradesView trades={recent} price={price} />
            )}
          </Card>

          {ticker && (
            <Card title="市场信息" className="h-fit">
              {(
                [
                  ["资金费率", `${(ticker.fundingRate * 100).toFixed(4)}%`, ticker.fundingRate >= 0 ? "pos" : "neg"],
                  ["下次结算", ticker.nextFundingIn, ""],
                  ["持仓量 OI", fmt(ticker.openInterest, 0), ""],
                  ["标记价格", fmt(ticker.markPrice, price > 1000 ? 1 : 3), ""],
                  ["指数价格", fmt(ticker.indexPrice, price > 1000 ? 1 : 3), ""],
                ] as const
              ).map(([l, v, tone], i, a) => (
                <div
                  key={l}
                  className={`flex justify-between py-2 text-xs ${i < a.length - 1 ? "border-b border-line-soft" : ""}`}
                >
                  <span className="text-fg-3">{l}</span>
                  <span
                    className={`font-mono font-semibold ${
                      tone === "pos" ? "text-mint" : tone === "neg" ? "text-rose" : "text-fg-1"
                    }`}
                  >
                    {v}
                  </span>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </PageShell>
  );
}
