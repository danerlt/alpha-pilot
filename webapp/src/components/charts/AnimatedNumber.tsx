/**
 * 数字滚动动效 + 涨跌闪色 —— 对齐设计稿 enhancements.jsx AnimatedNumber。
 * 健壮性约束：动画被打断时从「当前显示值」继续（而非上次完成值）；
 * 页面在后台（rAF 暂停）时直接落最终值，避免高频更新下数字冻结。
 */
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
  const shownRef = useRef(value); // 实际显示中的值（动画中间态也同步）
  const targetRef = useRef(value);
  const raf = useRef<number>(0);

  useEffect(() => {
    if (targetRef.current === value) return;
    const from = shownRef.current;
    const to = value;
    targetRef.current = to;
    const start = performance.now();
    setFlash(to >= from ? "up" : "down");

    const settle = () => {
      shownRef.current = to;
      setDisplay(to);
      setTimeout(() => setFlash(null), 400);
    };

    // 后台标签页 rAF 暂停：直接落值
    if (document.hidden) {
      settle();
      return;
    }

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const v = from + (to - from) * eased;
      shownRef.current = v;
      setDisplay(v);
      if (t < 1) {
        raf.current = requestAnimationFrame(tick);
      } else {
        settle();
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
