/** 交互式面积曲线（十字光标 + tooltip）—— 对齐设计稿 enhancements.jsx WSparkLive */
import { useEffect, useId, useRef, useState, type MouseEvent } from "react";
import { fmt, fmtPct } from "@/lib/format";

export function SparkLive({
  data,
  h = 160,
  color = "var(--ap-mint)",
  valuePrefix = "$",
}: {
  data: number[];
  h?: number;
  color?: string;
  valuePrefix?: string;
}) {
  const gid = useId();
  const wrapRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{ i: number; x: number; y: number; value: number } | null>(null);
  const [w, setW] = useState(700);

  useEffect(() => {
    const ro = new ResizeObserver((es) => {
      for (const e of es) setW(e.contentRect.width);
    });
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const r = max - min || 1;
  const px = (i: number) => (i / (data.length - 1)) * w;
  const py = (v: number) => h - ((v - min) / r) * (h - 16) - 8;
  const pts = data.map((v, i) => [px(i), py(v)] as const);
  const path = pts
    .map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1))
    .join(" ");
  const area = path + ` L ${w} ${h} L 0 ${h} Z`;

  const onMove = (e: MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const i = Math.max(
      0,
      Math.min(data.length - 1, Math.round((x / w) * (data.length - 1))),
    );
    setHover({ i, x: px(i), y: py(data[i]), value: data[i] });
  };

  const change = hover ? ((hover.value - data[0]) / data[0]) * 100 : null;

  return (
    <div ref={wrapRef} className="relative w-full select-none">
      <svg
        width="100%"
        height={h}
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
        className="block"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity=".32" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((t) => (
          <line key={t} x1="0" x2={w} y1={t * h} y2={t * h} stroke="var(--ap-line-soft)" strokeWidth="1" />
        ))}
        <path d={area} fill={`url(#${gid})`} />
        <path d={path} stroke={color} strokeWidth="1.8" fill="none" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
        {hover && (
          <g>
            <line x1={hover.x} x2={hover.x} y1="0" y2={h} stroke="var(--ap-fg-3)" strokeWidth="1" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
            <circle cx={hover.x} cy={hover.y} r="4" fill={color} stroke="var(--ap-bg-1)" strokeWidth="2" />
          </g>
        )}
      </svg>
      {hover && change !== null && (
        <div
          className="pointer-events-none absolute top-1.5 z-[2] -translate-x-1/2 whitespace-nowrap rounded-sm border border-line bg-bg-4 px-2.5 py-1.5 shadow-2"
          style={{ left: `${Math.max(4, Math.min((hover.x / w) * 100, 78))}%` }}
        >
          <div className="font-mono text-sm font-bold text-fg-1">
            {valuePrefix}
            {fmt(hover.value)}
          </div>
          <div className={`font-mono text-micro ${change >= 0 ? "text-mint" : "text-rose"}`}>
            {change >= 0 ? "▲" : "▼"} {fmtPct(change)} 自起点
          </div>
        </div>
      )}
    </div>
  );
}
