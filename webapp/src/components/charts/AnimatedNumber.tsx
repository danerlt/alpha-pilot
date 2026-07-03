/** 数字滚动动效 + 涨跌闪色 —— 对齐设计稿 enhancements.jsx AnimatedNumber */
import { useEffect, useRef, useState, type CSSProperties } from "react";

export function AnimatedNumber({
  value,
  format = (v: number) => v.toFixed(2),
  prefix = "",
  suffix = "",
  className = "",
  style,
  duration = 600,
}: {
  value: number;
  format?: (v: number) => string;
  prefix?: string;
  suffix?: string;
  className?: string;
  style?: CSSProperties;
  duration?: number;
}) {
  const [display, setDisplay] = useState(value);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const prev = useRef(value);
  const raf = useRef<number>(0);

  useEffect(() => {
    if (prev.current === value) return;
    const from = prev.current;
    const to = value;
    const start = performance.now();
    setFlash(to >= from ? "up" : "down");
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) {
        raf.current = requestAnimationFrame(tick);
      } else {
        prev.current = to;
        setTimeout(() => setFlash(null), 400);
      }
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [value, duration]);

  const flashColor =
    flash === "up"
      ? "var(--ap-mint)"
      : flash === "down"
        ? "var(--ap-rose)"
        : undefined;

  return (
    <span
      className={`inline-block font-mono ${className}`}
      style={{
        fontVariantNumeric: "tabular-nums",
        transition: "color .3s, transform .3s",
        transform: flash ? "scale(1.015)" : "scale(1)",
        ...style,
        ...(flashColor ? { color: flashColor } : {}),
      }}
    >
      {prefix}
      {format(display)}
      {suffix}
    </span>
  );
}
