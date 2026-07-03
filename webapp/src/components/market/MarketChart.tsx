/**
 * K线图 —— SVG 蜡烛 + 量能 + SL/TP/入场标线（远离现价钉边缘带 ↓）+ 现价 cyan 虚线 + 十字光标。
 * 对齐设计稿 market.jsx MarketChart；生产可换 lightweight-charts（handoff/02 P3 建议）。
 */
import { useEffect, useRef, useState, type MouseEvent } from "react";
import type { Kline, Position } from "@/api/types";
import { fmt } from "@/lib/format";

const H = 380;
const PAD = 16;
const VOL_H = 56;
const CHART_H = H - VOL_H - 24;

export function MarketChart({
  klines,
  price,
  position,
}: {
  klines: Kline[];
  price: number;
  position?: Position;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(760);
  const [hover, setHover] = useState<{ i: number; k: Kline; x: number } | null>(null);

  useEffect(() => {
    const ro = new ResizeObserver((es) => {
      for (const e of es) setW(e.contentRect.width);
    });
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  if (klines.length === 0) {
    return (
      <div className="flex h-[380px] items-center justify-center font-mono text-sm text-fg-4">
        加载 K 线…
      </div>
    );
  }

  const allP = klines.flatMap((k) => [k.h, k.l]);
  const min = Math.min(...allP);
  const max = Math.max(...allP);
  const r = max - min || 1;
  const y = (p: number) => PAD + (1 - (p - min) / r) * (CHART_H - PAD);
  // 远离现价的价位钉在图边缘，避免压扁蜡烛
  const yLvl = (p: number) => Math.max(PAD + 6, Math.min(CHART_H - 6, y(p)));
  const cw = (w - PAD * 2) / klines.length;
  const cx = (i: number) => PAD + i * cw + cw / 2;
  const maxV = Math.max(...klines.map((k) => k.v)) || 1;

  const onMove = (e: MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const i = Math.max(0, Math.min(klines.length - 1, Math.floor((x - PAD) / cw)));
    setHover({ i, k: klines[i], x: cx(i) });
  };

  const levels = position
    ? [
        { p: position.tp, c: "var(--ap-mint)", l: `TP ${fmt(position.tp, 0)}`, dash: false },
        { p: position.entry, c: "var(--ap-fg-3)", l: `入场 ${fmt(position.entry, 0)}`, dash: true },
        { p: position.sl, c: "var(--ap-rose)", l: `SL ${fmt(position.sl, 0)}`, dash: false },
      ]
    : [];

  return (
    <div ref={wrapRef} className="relative w-full">
      <svg
        width="100%"
        height={H}
        viewBox={`0 0 ${w} ${H}`}
        className="block"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        {/* 网格 */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <line key={t} x1={PAD} x2={w - PAD} y1={PAD + t * (CHART_H - PAD)} y2={PAD + t * (CHART_H - PAD)} stroke="var(--ap-line-soft)" />
        ))}
        {/* 价格轴 */}
        {[0, 0.5, 1].map((t, i) => (
          <text key={t} x={w - PAD} y={PAD + t * (CHART_H - PAD) + (i === 0 ? 10 : i === 2 ? -2 : 4)} textAnchor="end" fontSize="9.5" fill="var(--ap-fg-4)" fontFamily="var(--ap-font-mono)">
            {fmt(max - t * r, 0)}
          </text>
        ))}
        {/* 持仓标线 */}
        {levels.map((lv) => {
          const clamped = y(lv.p) !== yLvl(lv.p);
          const lw = clamped ? 64 : 52;
          return (
            <g key={lv.l}>
              <line x1={PAD} x2={w - PAD - lw} y1={yLvl(lv.p)} y2={yLvl(lv.p)} stroke={lv.c} strokeWidth="1" strokeDasharray={lv.dash || clamped ? "3 3" : "5 0"} opacity={clamped ? 0.5 : 0.75} />
              <rect x={w - PAD - lw} y={yLvl(lv.p) - 8} width={lw} height={16} rx={3} fill={lv.c} opacity=".18" />
              <text x={w - PAD - 4} y={yLvl(lv.p) + 4} textAnchor="end" fontSize="9" fill={lv.c} fontFamily="var(--ap-font-mono)" fontWeight="600">
                {lv.l}
                {clamped ? " ↓" : ""}
              </text>
            </g>
          );
        })}
        {/* 蜡烛 */}
        {klines.map((k, i) => {
          const up = k.c >= k.o;
          const col = up ? "var(--ap-mint)" : "var(--ap-rose)";
          const bw = Math.max(1.5, cw * 0.62);
          return (
            <g key={k.t}>
              <line x1={cx(i)} x2={cx(i)} y1={y(k.h)} y2={y(k.l)} stroke={col} strokeWidth="1" />
              <rect x={cx(i) - bw / 2} y={y(Math.max(k.o, k.c))} width={bw} height={Math.max(1, Math.abs(y(k.o) - y(k.c)))} fill={col} opacity={up ? 0.95 : 0.9} />
            </g>
          );
        })}
        {/* 现价线 */}
        <line x1={PAD} x2={w - PAD - 52} y1={yLvl(price)} y2={yLvl(price)} stroke="var(--ap-cyan)" strokeWidth="1" strokeDasharray="1 3" />
        <rect x={w - PAD - 52} y={yLvl(price) - 8} width={52} height={16} rx={3} fill="var(--ap-cyan)" />
        <text x={w - PAD - 4} y={yLvl(price) + 4} textAnchor="end" fontSize="9.5" fill="var(--ap-bg-0)" fontFamily="var(--ap-font-mono)" fontWeight="700">
          {fmt(price, 0)}
        </text>
        {/* 量能 */}
        <g transform={`translate(0,${H - VOL_H})`}>
          {klines.map((k, i) => {
            const up = k.c >= k.o;
            const bw = Math.max(1.5, cw * 0.62);
            const vh = (k.v / maxV) * (VOL_H - 8);
            return <rect key={k.t} x={cx(i) - bw / 2} y={VOL_H - vh} width={bw} height={vh} fill={up ? "var(--ap-mint)" : "var(--ap-rose)"} opacity=".35" />;
          })}
        </g>
        {/* 十字光标 */}
        {hover && (
          <>
            <line x1={hover.x} x2={hover.x} y1={PAD} y2={CHART_H} stroke="var(--ap-fg-3)" strokeWidth="1" strokeDasharray="3 3" />
            <circle cx={hover.x} cy={y(hover.k.c)} r="3.5" fill="var(--ap-cyan)" stroke="var(--ap-bg-1)" strokeWidth="2" />
          </>
        )}
      </svg>
      {hover && (
        <div
          className="pointer-events-none absolute top-2 z-[2] -translate-x-1/2 whitespace-nowrap rounded-sm border border-line bg-bg-4 px-[11px] py-[7px] font-mono text-xs shadow-2"
          style={{ left: `${Math.max(8, Math.min((hover.x / w) * 100, 72))}%` }}
        >
          <div className="flex gap-3">
            <span className="text-fg-3">O</span>
            <span className="text-fg-1">{fmt(hover.k.o, 0)}</span>
            <span className="text-fg-3">H</span>
            <span className="text-mint">{fmt(hover.k.h, 0)}</span>
          </div>
          <div className="mt-0.5 flex gap-3">
            <span className="text-fg-3">C</span>
            <span className={hover.k.c >= hover.k.o ? "text-mint" : "text-rose"}>{fmt(hover.k.c, 0)}</span>
            <span className="text-fg-3">L</span>
            <span className="text-rose">{fmt(hover.k.l, 0)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
