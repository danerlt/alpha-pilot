/**
 * 原子组件 —— 对齐设计稿 shell.jsx 的 WPill/WDot/WCard/WStat。
 * 色彩纪律：涨跌色只用于真实数值正负；violet 仅 AI 产物；数字一律 mono。
 */
import type { CSSProperties, ReactNode } from "react";

export type Tone = "mint" | "rose" | "amber" | "violet" | "cyan" | "default";

const pillTones: Record<Tone, string> = {
  mint: "bg-mint-soft text-mint",
  rose: "bg-rose-soft text-rose",
  amber: "bg-amber-soft text-amber",
  violet: "bg-violet-soft text-violet",
  cyan: "bg-cyan-soft text-cyan",
  default: "bg-bg-3 text-fg-2",
};

export function Pill({
  children,
  tone = "default",
  className = "",
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-pill px-2 py-0.5 font-mono text-[10.5px] font-semibold tracking-[.04em] ${pillTones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

export function Dot({
  color,
  glow = false,
  size = 6,
  pulse = false,
}: {
  color: string;
  glow?: boolean;
  size?: number;
  pulse?: boolean;
}) {
  return (
    <span
      className={`inline-block shrink-0 rounded-full ${pulse ? "ap-pulse" : ""}`}
      style={{
        width: size,
        height: size,
        background: color,
        boxShadow: glow ? `0 0 6px ${color}` : "none",
      }}
    />
  );
}

export function Card({
  children,
  title,
  right,
  dense = false,
  glow = false,
  className = "",
  bodyClassName = "",
  style,
}: {
  children: ReactNode;
  title?: ReactNode;
  right?: ReactNode;
  dense?: boolean;
  glow?: boolean;
  className?: string;
  bodyClassName?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      className={`overflow-hidden rounded-md border border-line-soft bg-bg-2 ${className}`}
      style={{
        ...(glow
          ? {
              boxShadow:
                "0 0 0 1px var(--ap-violet), 0 0 40px rgba(124,92,255,.12)",
            }
          : {}),
        ...style,
      }}
    >
      {title !== undefined && (
        <div
          className={`flex items-center justify-between border-b border-line-soft ${dense ? "px-3.5 py-2.5" : "px-[18px] py-3.5"}`}
        >
          <div className="truncate text-xs font-semibold uppercase tracking-[.08em] text-fg-3">
            {title}
          </div>
          {right}
        </div>
      )}
      <div className={bodyClassName || (dense ? "px-3.5 py-3" : "px-[18px] py-4")}>
        {children}
      </div>
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  tone,
  size = "md",
}: {
  label: ReactNode;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "pos" | "neg" | "ai";
  size?: "sm" | "md" | "lg";
}) {
  const fs = size === "lg" ? 28 : size === "sm" ? 16 : 22;
  const color =
    tone === "pos"
      ? "text-mint"
      : tone === "neg"
        ? "text-rose"
        : tone === "ai"
          ? "text-violet"
          : "text-fg-1";
  return (
    <div className="flex flex-col gap-1">
      <div className="text-[10.5px] font-medium uppercase tracking-[.08em] text-fg-3">
        {label}
      </div>
      <div
        className={`font-mono font-bold leading-[1.1] tracking-[-.02em] ${color}`}
        style={{ fontSize: fs }}
      >
        {value}
      </div>
      {sub && <div className="font-mono text-[11.5px] text-fg-3">{sub}</div>}
    </div>
  );
}

/** 涨/跌数值取色（色彩纪律：只用于真实正负值） */
export function pnlTone(n: number): "pos" | "neg" | undefined {
  if (n > 0) return "pos";
  if (n < 0) return "neg";
  return undefined;
}

export function pnlClass(n: number): string {
  return n > 0 ? "text-mint" : n < 0 ? "text-rose" : "text-fg-2";
}
