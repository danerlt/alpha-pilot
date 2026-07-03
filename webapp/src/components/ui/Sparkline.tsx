/** SVG 迷你曲线 —— 对齐设计稿 WSpark；带渐变填充 */
import { useId } from "react";

export function Sparkline({
  data,
  w = 400,
  h = 110,
  color = "var(--ap-mint)",
  fill = true,
  strokeWidth = 1.8,
  className = "",
}: {
  data: number[];
  w?: number;
  h?: number;
  color?: string;
  fill?: boolean;
  strokeWidth?: number;
  className?: string;
}) {
  const gid = useId();
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const r = max - min || 1;
  const pts = data.map(
    (v, i) =>
      [
        (i / (data.length - 1)) * w,
        h - ((v - min) / r) * (h - 8) - 4,
      ] as const,
  );
  const path = pts
    .map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1))
    .join(" ");
  const area = path + ` L ${w} ${h} L 0 ${h} Z`;
  return (
    <svg
      width="100%"
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      className={`block ${className}`}
    >
      <defs>
        <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity=".35" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={area} fill={`url(#${gid})`} />}
      <path
        d={path}
        stroke={color}
        strokeWidth={strokeWidth}
        fill="none"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
