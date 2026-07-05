/**
 * K 线图（lightweight-charts，handoff/02 P3 生产方案）——
 * 蜡烛 + 量能 + SL/TP/入场价格线 + 现价虚线 + 十字光标 OHLC 图例。
 * 颜色全部运行时解析自 --ap-* token，保持零硬编码色值纪律。
 */
import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  CrosshairMode,
  HistogramSeries,
  LineStyle,
  createChart,
  type CandlestickData,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Kline, Position } from "@/api/types";
import { fmt } from "@/lib/format";

function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function KlineChart({
  klines,
  position,
}: {
  klines: Kline[];
  position?: Position;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);
  const [legend, setLegend] = useState<CandlestickData | null>(null);

  // 建图（一次）
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const mint = token("--ap-mint");
    const rose = token("--ap-rose");
    const cyan = token("--ap-cyan");
    const fg3 = token("--ap-fg-3");
    const fg4 = token("--ap-fg-4");
    const lineSoft = token("--ap-line-soft");
    const line = token("--ap-line");

    const chart = createChart(el, {
      width: el.clientWidth || 600,
      height: el.clientHeight || 380,
      layout: {
        background: { color: "transparent" },
        textColor: fg4,
        fontFamily: token("--ap-font-mono") || "monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: lineSoft },
        horzLines: { color: lineSoft },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: fg3, style: LineStyle.Dashed, labelBackgroundColor: token("--ap-bg-4") },
        horzLine: { color: fg3, style: LineStyle.Dashed, labelBackgroundColor: token("--ap-bg-4") },
      },
      rightPriceScale: { borderColor: line },
      timeScale: { borderColor: line, timeVisible: true, secondsVisible: false },
    });

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: mint,
      downColor: rose,
      borderUpColor: mint,
      borderDownColor: rose,
      wickUpColor: mint,
      wickDownColor: rose,
      priceLineVisible: true,
      priceLineColor: cyan,
      priceLineStyle: LineStyle.SparseDotted,
    });
    const volume = chart.addSeries(HistogramSeries, {
      priceScaleId: "vol",
      priceFormat: { type: "volume" },
      lastValueVisible: false,
      priceLineVisible: false,
    });
    chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    chart.subscribeCrosshairMove((param) => {
      const d = param.seriesData.get(candles) as CandlestickData | undefined;
      setLegend(d ?? null);
    });

    // 显式尺寸驱动（autoSize 在部分嵌套 flex/grid 布局下测量不稳，见走查记录）
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        chart.applyOptions({
          width: Math.floor(e.contentRect.width),
          height: Math.floor(e.contentRect.height),
        });
      }
    });
    ro.observe(el);

    chartRef.current = chart;
    candleRef.current = candles;
    volumeRef.current = volume;
    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      priceLinesRef.current = [];
    };
  }, []);

  // 数据更新
  useEffect(() => {
    const candles = candleRef.current;
    const volume = volumeRef.current;
    if (!candles || !volume || klines.length === 0) return;
    const mintSoft = token("--ap-mint-soft");
    const roseSoft = token("--ap-rose-soft");
    candles.setData(
      klines.map((k) => ({
        time: (k.t / 1000) as UTCTimestamp,
        open: k.o,
        high: k.h,
        low: k.l,
        close: k.c,
      })),
    );
    volume.setData(
      klines.map((k) => ({
        time: (k.t / 1000) as UTCTimestamp,
        value: k.v,
        color: k.c >= k.o ? mintSoft : roseSoft,
      })),
    );
    chartRef.current?.timeScale().fitContent();
  }, [klines]);

  // SL/TP/入场标线
  useEffect(() => {
    const candles = candleRef.current;
    if (!candles) return;
    priceLinesRef.current.forEach((l) => candles.removePriceLine(l));
    priceLinesRef.current = [];
    if (!position) return;
    const mk = (price: number, color: string, title: string, dashed: boolean) =>
      candles.createPriceLine({
        price,
        color,
        lineWidth: 1,
        lineStyle: dashed ? LineStyle.Dashed : LineStyle.Solid,
        axisLabelVisible: true,
        title,
      });
    priceLinesRef.current = [
      mk(position.tp, token("--ap-mint"), "TP", false),
      mk(position.entry, token("--ap-fg-3"), "入场", true),
      mk(position.sl, token("--ap-rose"), "SL", false),
    ];
  }, [position, klines.length]);

  return (
    <div className="relative h-[380px] w-full">
      <div ref={containerRef} className="absolute inset-0" />
      {klines.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center font-mono text-sm text-fg-4">
          加载 K 线…
        </div>
      )}
      {legend && (
        <div className="pointer-events-none absolute left-2 top-2 z-[2] flex gap-3 rounded-sm border border-line bg-bg-4/90 px-2.5 py-1.5 font-mono text-xs shadow-2">
          <span>
            <span className="text-fg-3">O </span>
            <span className="text-fg-1">{fmt(legend.open, 0)}</span>
          </span>
          <span>
            <span className="text-fg-3">H </span>
            <span className="text-mint">{fmt(legend.high, 0)}</span>
          </span>
          <span>
            <span className="text-fg-3">L </span>
            <span className="text-rose">{fmt(legend.low, 0)}</span>
          </span>
          <span>
            <span className="text-fg-3">C </span>
            <span className={legend.close >= legend.open ? "text-mint" : "text-rose"}>
              {fmt(legend.close, 0)}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
