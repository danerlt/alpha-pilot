/**
 * AI 决策卡 —— 3 变体（stepper/timeline/graph），对齐设计稿 ai_card.jsx。
 * violet 纪律：仅 AI 产物使用 violet。
 */
import {
  AlertTriangle,
  BrainCircuit,
  Check,
  Play,
  Shield,
  X,
  Zap,
} from "lucide-react";
import type { Decision } from "@/api/types";
import { fmt } from "@/lib/format";
import { Card, Dot, Pill } from "@/components/ui/atoms";
import type { CardVariant } from "./variant";

const actionColor = (d: Decision) =>
  d.action === "OPEN_LONG"
    ? "text-mint"
    : d.action === "CLOSE_LONG"
      ? "text-rose"
      : "text-fg-2";

const guardTone = (d: Decision) =>
  d.guard === "PASS" ? "mint" : d.guard === "REJECT" ? "rose" : "amber";

const guardVar = (d: Decision) =>
  d.guard === "PASS"
    ? "var(--ap-mint)"
    : d.guard === "DEGRADE"
      ? "var(--ap-amber)"
      : "var(--ap-rose)";

function CardHeader({ d, tag }: { d: Decision; tag?: string }) {
  return (
    <div className="mb-3.5 flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-violet-soft">
          <BrainCircuit size={16} className="text-violet" />
        </div>
        <div>
          <div className="text-[10.5px] font-bold tracking-[.1em] text-violet">
            AI DECISION{tag ? ` · ${tag}` : ""}
          </div>
          <div className="font-mono text-xs tracking-[.02em] text-fg-3">
            {d.id} · {d.symbol} · {d.timeframe} · {d.ts}
          </div>
        </div>
      </div>
      <div className="flex items-baseline gap-2.5">
        <span className={`font-mono text-h2 font-bold tracking-[.02em] ${actionColor(d)}`}>
          {d.action}
        </span>
        <span className="font-mono text-xs text-fg-3">
          conf <b className="text-fg-1">{d.confidence.toFixed(2)}</b>
        </span>
      </div>
    </div>
  );
}

function Reasoning({ d }: { d: Decision }) {
  return (
    <div className="rounded-[10px] bg-bg-3 px-3.5 py-3 text-sm leading-relaxed text-fg-2">
      <div className="mb-1.5 text-micro font-bold tracking-[.08em] text-violet">
        REASONING
      </div>
      {d.reason}
    </div>
  );
}

// ============ 变体 A：Stepper（横向流水线） ============
function Stepper({ d }: { d: Decision }) {
  const steps = [
    { label: "市场快照", sub: "regime · features", ok: true, degraded: false },
    { label: "AI 推理", sub: `conf ${d.confidence.toFixed(2)}`, ok: true, degraded: false },
    { label: "守卫检查", sub: d.guard, ok: d.guard !== "REJECT", degraded: d.guard === "DEGRADE" },
    { label: "风险裁决", sub: d.guard === "PASS" ? "允许执行" : "回退 HOLD", ok: d.guard === "PASS", degraded: false },
    { label: "执行", sub: d.guard === "PASS" ? "已下单" : "未执行", ok: d.guard === "PASS", degraded: false },
  ];
  return (
    <Card glow>
      <CardHeader d={d} />

      {d.sl !== undefined && (
        <div className="mb-3.5 grid grid-cols-5 gap-px overflow-hidden rounded-[10px] bg-bg-3">
          {(
            [
              ["策略", d.strategy, "text-fg-1"],
              ["入场", d.entry !== undefined ? fmt(d.entry) : "—", "text-fg-1"],
              ["仓位", d.sizePct ?? "—", "text-fg-1"],
              ["止损", fmt(d.sl), "text-rose"],
              ["止盈", d.tp !== undefined ? fmt(d.tp) : "—", "text-mint"],
            ] as const
          ).map(([l, v, c]) => (
            <div key={l} className="bg-bg-2 px-3 py-2.5">
              <div className="mb-[3px] text-[9.5px] uppercase tracking-[.08em] text-fg-3">
                {l}
              </div>
              <div className={`font-mono text-sm font-semibold ${c}`}>{v}</div>
            </div>
          ))}
        </div>
      )}

      {/* 流水线 */}
      <div className="flex items-center overflow-x-auto pb-4 pt-1.5">
        {steps.map((step, i) => {
          const c = step.ok
            ? "var(--ap-mint)"
            : step.degraded
              ? "var(--ap-amber)"
              : "var(--ap-rose)";
          return (
            <div key={step.label} className="contents">
              <div className="flex w-[100px] shrink-0 flex-col items-center gap-2">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-full"
                  style={{ background: c, boxShadow: `0 0 12px ${c}66` }}
                >
                  {step.ok ? (
                    <Check size={15} strokeWidth={2.4} style={{ color: "var(--ap-bg-0)" }} />
                  ) : step.degraded ? (
                    <AlertTriangle size={15} strokeWidth={2.4} style={{ color: "var(--ap-bg-0)" }} />
                  ) : (
                    <X size={15} strokeWidth={2.4} style={{ color: "var(--ap-bg-0)" }} />
                  )}
                </div>
                <div className="text-center">
                  <div className="text-xs font-semibold text-fg-1">{step.label}</div>
                  <div className="mt-0.5 font-mono text-[10.5px] text-fg-3">{step.sub}</div>
                </div>
              </div>
              {i < steps.length - 1 && (
                <div
                  className="-mt-[30px] h-0.5 min-w-3 flex-1 opacity-55"
                  style={{ background: c }}
                />
              )}
            </div>
          );
        })}
      </div>

      <Reasoning d={d} />

      <div className="mt-3.5 flex items-center gap-2">
        <Pill tone={guardTone(d)}>守卫 {d.guard}</Pill>
        {d.features && <Pill tone="violet">{d.features.length} features</Pill>}
        {d.guards && (
          <Pill>
            {d.guards.filter((g) => g.ok).length}/{d.guards.length} checks
          </Pill>
        )}
        <span className="ml-auto font-mono text-xs text-fg-4">
          trace · {d.id.replace("d_", "")}
        </span>
      </div>
    </Card>
  );
}

// ============ 变体 B：Timeline（纵向时间线） ============
function Timeline({ d }: { d: Decision }) {
  const gc = guardVar(d);
  const stages = [
    { label: "信号感知", detail: `regime 判定 · ${d.symbol} ${d.timeframe} 特征采集`, color: "var(--ap-cyan)", icon: Zap },
    { label: "AI 推理", detail: `${d.strategy} · 置信度 ${d.confidence.toFixed(2)} · 输出 ${d.action}`, color: "var(--ap-violet)", icon: BrainCircuit },
    { label: "守卫检查", detail: d.guards ? `${d.guards.filter((g) => g.ok).length}/${d.guards.length} 通过` : d.guard, color: gc, icon: Shield },
    { label: "风险裁决", detail: d.guard === "PASS" ? `允许执行 · 下单 ${d.sizePct ?? ""}` : "回退 HOLD · 不下单", color: d.guard === "PASS" ? "var(--ap-mint)" : "var(--ap-rose)", icon: Check },
    { label: "执行", detail: d.guard === "PASS" ? `Binance 市价成交 @ ${fmt(d.entry ?? 0)}` : "—", color: d.guard === "PASS" ? "var(--ap-mint)" : "var(--ap-fg-4)", icon: Play },
  ];
  return (
    <Card glow>
      <CardHeader d={d} tag="TIMELINE" />
      <div className="relative pl-1">
        {stages.map((s, i) => (
          <div
            key={s.label}
            className={`relative flex gap-3.5 ${i === stages.length - 1 ? "" : "pb-3.5"}`}
          >
            {i < stages.length - 1 && (
              <div
                className="absolute -bottom-1 left-[11px] top-[26px] w-[1.5px] opacity-50"
                style={{
                  background: `linear-gradient(to bottom, ${s.color} 0%, var(--ap-line) 100%)`,
                }}
              />
            )}
            <div
              className="z-[1] flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
              style={{ background: s.color, boxShadow: `0 0 10px ${s.color}40` }}
            >
              <s.icon size={12} strokeWidth={2.2} style={{ color: "var(--ap-bg-0)" }} />
            </div>
            <div className="flex-1 pt-0.5">
              <div className="mb-0.5 flex items-baseline gap-2">
                <span className="text-sm font-semibold text-fg-1">{s.label}</span>
                <span className="ml-auto font-mono text-micro text-fg-4">{d.ts}</span>
              </div>
              <div className="font-mono text-xs text-fg-3">{s.detail}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4">
        <Reasoning d={d} />
      </div>
    </Card>
  );
}

// ============ 变体 C：Graph（节点图） ============
const FALLBACK_FEATURES = [
  { k: "regime", v: "trending_up", ok: true },
  { k: "EMA_align", v: "20>50>200", ok: true },
  { k: "vol_mult", v: "1.4x", ok: true },
  { k: "ATR_14", v: "1.82%", ok: true },
  { k: "RSI_14", v: "58", ok: true },
  { k: "BB_width", v: "0.043", ok: true },
];

const FALLBACK_GUARDS = [
  "regime_match",
  "max_per_trade_risk",
  "max_position_size",
  "daily_loss_limit",
  "RR_ratio",
  "correlation_cap",
  "spread_check",
  "cooldown",
].map((k) => ({ k, ok: true, note: "" }));

function Graph({ d }: { d: Decision }) {
  const guardPass = d.guard === "PASS";
  const gc = guardVar(d);
  const features = (d.features ?? FALLBACK_FEATURES).slice(0, 6);
  const guards = d.guards ?? FALLBACK_GUARDS;
  return (
    <Card glow>
      <CardHeader d={d} tag="GRAPH" />
      <div className="overflow-x-auto">
        <div className="relative min-h-[360px] min-w-[960px] overflow-hidden rounded-md bg-bg-3 p-5">
          {/* 网格底纹 */}
          <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-25">
            <defs>
              <pattern id="ap-gd" width="24" height="24" patternUnits="userSpaceOnUse">
                <path d="M 24 0 L 0 0 0 24" fill="none" stroke="var(--ap-line)" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#ap-gd)" />
          </svg>

          {/* 连线 */}
          <svg className="pointer-events-none absolute inset-0 h-full w-full">
            <defs>
              <marker id="ap-arrow-mint" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ap-mint)" />
              </marker>
              <marker id="ap-arrow-v" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ap-violet)" />
              </marker>
            </defs>
            {[60, 110, 160, 210, 260, 310].map((y) => (
              <path key={y} d={`M 180 ${y} C 240 ${y}, 260 180, 310 180`} stroke="var(--ap-cyan)" strokeWidth="1" strokeOpacity=".55" fill="none" />
            ))}
            <path d="M 480 180 L 560 180" stroke="var(--ap-violet)" strokeWidth="2" fill="none" markerEnd="url(#ap-arrow-v)" />
            {[60, 100, 140, 180, 220, 260, 300, 340].map((y) => (
              <path key={y} d={`M 680 ${y} C 640 ${y}, 620 180, 640 180`} stroke={gc} strokeWidth="1" strokeOpacity=".5" fill="none" />
            ))}
            <path d="M 740 180 L 820 180" stroke={gc} strokeWidth="2.5" fill="none" markerEnd={guardPass ? "url(#ap-arrow-mint)" : undefined} />
          </svg>

          {/* FEATURES 列 */}
          <div className="absolute left-5 top-5 flex w-[160px] flex-col gap-1.5">
            <div className="mb-0.5 text-[9.5px] uppercase tracking-[.08em] text-fg-3">
              FEATURES
            </div>
            {features.map((f) => (
              <div key={f.k} className="flex justify-between gap-2 rounded-xs border border-line-soft bg-bg-2 px-2 py-[5px] font-mono text-[10.5px]">
                <span className="text-fg-3">{f.k}</span>
                <span className="text-cyan">{f.v}</span>
              </div>
            ))}
          </div>

          {/* AI hub */}
          <div
            className="absolute left-[310px] top-[140px] w-[170px] rounded-md border border-violet bg-violet-soft p-3.5"
            style={{ boxShadow: "0 0 24px rgba(124,92,255,.3)" }}
          >
            <div className="mb-1.5 flex items-center gap-2">
              <BrainCircuit size={16} className="text-violet" />
              <span className="text-xs font-bold tracking-[.05em] text-violet">
                LLM + RULES
              </span>
            </div>
            <div className="text-xs text-fg-2">{d.strategy}</div>
            <div className="mt-1.5 font-mono text-xs text-fg-3">
              conf <b className="text-violet">{d.confidence.toFixed(2)}</b> · {d.action}
            </div>
          </div>

          {/* Guard hub */}
          <div
            className="absolute left-[560px] top-[155px] w-20 rounded-md border bg-bg-2 p-3 text-center"
            style={{ borderColor: gc, boxShadow: `0 0 20px ${gc}30` }}
          >
            <Shield size={18} className="mx-auto" style={{ color: gc }} />
            <div className="mt-1 font-mono text-micro font-bold tracking-[.05em]" style={{ color: gc }}>
              {d.guard}
            </div>
          </div>

          {/* GUARDS 列 */}
          <div className="absolute left-[680px] top-5 flex w-[150px] flex-col gap-1">
            <div className="mb-0.5 text-[9.5px] uppercase tracking-[.08em] text-fg-3">
              GUARDS · {guards.length}
            </div>
            {guards.map((g) => (
              <div key={g.k} className="flex items-center gap-1.5 rounded-xs border border-line-soft bg-bg-2 px-2 py-1 font-mono text-micro">
                <Dot color={g.ok ? "var(--ap-mint)" : "var(--ap-rose)"} />
                <span className="flex-1 truncate text-fg-3">{g.k}</span>
              </div>
            ))}
          </div>

          {/* EXECUTE 输出 */}
          <div
            className={`absolute left-[820px] top-[155px] rounded-md border px-3.5 py-3 text-center ${
              guardPass ? "border-mint bg-mint-soft" : "border-rose bg-rose-soft"
            }`}
          >
            <div className={`text-[9.5px] font-bold tracking-[.08em] ${guardPass ? "text-mint" : "text-rose"}`}>
              EXECUTE
            </div>
            <div className={`mt-[3px] font-mono text-sm font-bold ${guardPass ? "text-mint" : "text-rose"}`}>
              {guardPass ? d.action : "HOLD"}
            </div>
          </div>
        </div>
      </div>
      <div className="mt-3.5">
        <Reasoning d={d} />
      </div>
    </Card>
  );
}

export function DecisionCard({
  d,
  variant = "stepper",
}: {
  d: Decision;
  variant?: CardVariant;
}) {
  if (variant === "timeline") return <Timeline d={d} />;
  if (variant === "graph") return <Graph d={d} />;
  return <Stepper d={d} />;
}
