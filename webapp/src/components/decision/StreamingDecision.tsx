/**
 * 流式决策 —— 逐段点亮决策管道后展开完整卡片，可重放。
 * 对齐设计稿 enhancements.jsx StreamingDecision；真后端由 WS decision.progress 驱动。
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { BrainCircuit, Check, Play, Shield, Zap } from "lucide-react";
import type { Decision } from "@/api/types";
import { Card } from "@/components/ui/atoms";
import { DecisionCard } from "./DecisionCard";
import type { CardVariant } from "./variant";

const STAGES = [
  { k: "snapshot", label: "采集市场快照", detail: "regime · K线 · 特征因子", color: "var(--ap-cyan)", icon: Zap, ms: 700 },
  { k: "reason", label: "AI 推理中", detail: "LLM + 规则引擎评估", color: "var(--ap-violet)", icon: BrainCircuit, ms: 1100 },
  { k: "guard", label: "守卫检查", detail: "8 项硬风控校验", color: "var(--ap-mint)", icon: Shield, ms: 800 },
  { k: "verdict", label: "风险裁决", detail: "允许 / 回退 HOLD", color: "var(--ap-mint)", icon: Check, ms: 600 },
  { k: "exec", label: "执行下单", detail: "Binance 市价 + SL/TP", color: "var(--ap-mint)", icon: Play, ms: 700 },
];

export function StreamingDecision({
  d,
  variant,
  motion = true,
}: {
  d: Decision;
  variant: CardVariant;
  motion?: boolean;
}) {
  const [stage, setStage] = useState(motion ? -1 : 99);
  const [done, setDone] = useState(!motion);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const play = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setDone(false);
    setStage(0);
    let acc = 0;
    STAGES.forEach((s, i) => {
      acc += s.ms;
      timers.current.push(
        setTimeout(() => {
          if (i === STAGES.length - 1) {
            setStage(99);
            setDone(true);
          } else {
            setStage(i + 1);
          }
        }, acc),
      );
    });
  }, []);

  useEffect(() => {
    if (motion) {
      play();
    } else {
      setStage(99);
      setDone(true);
    }
    return () => timers.current.forEach(clearTimeout);
  }, [motion, d.id, play]);

  if (done) {
    return (
      <div className="relative">
        {motion && (
          <button
            onClick={play}
            title="重放决策过程"
            className="absolute right-4 top-3.5 z-[5] flex cursor-pointer items-center gap-1.5 rounded-[7px] border border-line bg-bg-3 px-2.5 py-[5px] font-mono text-xs text-fg-3 hover:text-fg-1"
          >
            <Play size={11} /> 重放
          </button>
        )}
        <DecisionCard d={d} variant={variant} />
      </div>
    );
  }

  return (
    <Card glow>
      <div className="mb-[18px] flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-violet-soft">
          <BrainCircuit size={16} className="text-violet" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 text-[10.5px] font-bold tracking-[.1em] text-violet">
            AI DECISION
            <span className="inline-flex gap-[3px]">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="h-1 w-1 rounded-full bg-violet"
                  style={{ animation: `apblink 1s ${i * 0.18}s infinite` }}
                />
              ))}
            </span>
          </div>
          <div className="font-mono text-xs text-fg-3">
            {d.symbol} · {d.timeframe} · 实时推理中…
          </div>
        </div>
      </div>

      <div className="relative flex flex-col gap-0.5 pl-1">
        {STAGES.map((s, i) => {
          const active = i === stage;
          const complete = i < stage;
          const pending = i > stage;
          return (
            <div
              key={s.k}
              className="relative flex gap-3.5 py-2.5 transition-opacity duration-300"
              style={{ opacity: pending ? 0.35 : 1 }}
            >
              {i < STAGES.length - 1 && (
                <div
                  className="absolute -bottom-1 left-[13px] top-[30px] w-[1.5px] opacity-50"
                  style={{ background: complete ? s.color : "var(--ap-line)" }}
                />
              )}
              <div
                className="z-[1] flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full"
                style={{
                  background: complete ? s.color : "var(--ap-bg-3)",
                  border: active
                    ? `2px solid ${s.color}`
                    : complete
                      ? "none"
                      : "1px solid var(--ap-line)",
                  boxShadow: active ? `0 0 14px ${s.color}66` : "none",
                  animation: active ? "appulse 1.2s infinite" : "none",
                }}
              >
                {complete ? (
                  <Check size={13} strokeWidth={2.6} style={{ color: "var(--ap-bg-0)" }} />
                ) : (
                  <s.icon
                    size={12}
                    strokeWidth={2}
                    style={{ color: active ? s.color : "var(--ap-fg-4)" }}
                  />
                )}
              </div>
              <div className="flex-1 pt-0.5">
                <div
                  className="text-sm font-semibold"
                  style={{ color: active ? s.color : "var(--ap-fg-1)" }}
                >
                  {s.label}
                  {active && <span className="font-mono font-normal"> …</span>}
                </div>
                <div className="mt-px font-mono text-[11.5px] text-fg-3">
                  {s.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
