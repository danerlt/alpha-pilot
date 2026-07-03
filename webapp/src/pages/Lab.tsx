/**
 * 策略实验室（handoff/02 P8）—— 受控进化流水线图示 + 候选卡（影子进度/对比/门槛）+ 进化历史。
 */
import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp, FlaskConical, Layers, Pause } from "lucide-react";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Pill } from "@/components/ui/atoms";
import { labApi } from "@/api/services";
import type { LabCandidate, LabHistoryItem, LabStage } from "@/api/types";

const STAGE_CFG: Record<LabStage, { l: string; tone: "violet" | "default" | "amber" | "mint" }> = {
  shadow: { l: "SHADOW 影子运行", tone: "violet" },
  queued: { l: "QUEUED 排队中", tone: "default" },
  canary: { l: "CANARY 灰度", tone: "amber" },
  live: { l: "LIVE 线上", tone: "mint" },
  retired: { l: "RETIRED 归档", tone: "default" },
};

function CandidateCard({ c }: { c: LabCandidate }) {
  const isQueued = c.stage === "queued";
  const better = c.metrics.filter((m) => m.better === "shadow").length >
    c.metrics.filter((m) => m.better === "live").length;
  return (
    <Card
      style={better ? { borderColor: "rgba(124,92,255,.4)" } : undefined}
    >
      {/* 头部 */}
      <div className="mb-3 flex items-start gap-3">
        <div className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[9px] bg-violet-soft">
          <Layers size={16} className="text-violet" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-bold text-fg-1">{c.title}</span>
            <Pill tone={STAGE_CFG[c.stage].tone}>{STAGE_CFG[c.stage].l}</Pill>
            {better && !isQueued && <Pill tone="mint">优于线上</Pill>}
          </div>
          <div className="mt-0.5 font-mono text-xs text-fg-4">
            {c.id} · 提交于 {c.createdAt} · 来源{" "}
            {c.source === "ai" ? "AI 复盘提案" : "人工提案"}
          </div>
        </div>
      </div>

      {isQueued ? (
        <div className="flex items-center gap-2.5">
          <div className="flex-1 text-xs text-fg-3">等待影子槽位 · 预计明日开始 14 天影子运行</div>
          <button className="cursor-pointer rounded-sm border border-violet bg-violet-soft px-3.5 py-2 text-xs font-semibold text-violet">
            立即开始
          </button>
        </div>
      ) : (
        <>
          {/* 影子进度 */}
          <div className="mb-3">
            <div className="mb-[5px] flex justify-between font-mono text-[10.5px] text-fg-3">
              <span>影子运行 第 {c.shadowDays}/14 天</span>
              <span>{c.shadowProgressPct}%</span>
            </div>
            <div className="h-[5px] overflow-hidden rounded-[3px] bg-bg-3">
              <div
                className="h-full rounded-[3px] bg-violet"
                style={{
                  width: `${c.shadowProgressPct}%`,
                  boxShadow: "0 0 8px var(--ap-violet-glow)",
                }}
              />
            </div>
          </div>

          {/* 影子 vs 线上 */}
          <div className="grid grid-cols-[90px_1fr_1fr] gap-2 pb-1.5 pt-1 text-micro uppercase tracking-[.06em] text-fg-4">
            <span />
            <span className="text-violet">影子 (模拟)</span>
            <span>线上 (真实)</span>
          </div>
          {c.metrics.map((m) => (
            <div
              key={m.k}
              className="grid grid-cols-[90px_1fr_1fr] items-center gap-2 border-b border-line-soft py-[7px] text-[11.5px]"
            >
              <span className="text-fg-4">{m.k}</span>
              <span
                className={`font-mono font-semibold ${
                  m.better === "shadow" ? "text-mint" : "text-fg-1"
                }`}
              >
                {m.shadow}
                {m.better === "shadow" && " ▲"}
              </span>
              <span className="font-mono text-fg-3">
                {m.live}
                {m.better === "live" && " ▲"}
              </span>
            </div>
          ))}

          {/* 操作（门槛逻辑：服务端校验，前端只做展示禁用） */}
          <div className="mt-3.5 flex items-center gap-2">
            {c.promotable ? (
              <button className="cursor-pointer rounded-[9px] border-none bg-mint px-4 py-[9px] text-xs font-bold text-bg-0 hover:brightness-110">
                申请灰度上线 →
              </button>
            ) : (
              <button
                disabled
                className="cursor-not-allowed rounded-[9px] border border-line bg-bg-3 px-4 py-[9px] text-xs font-semibold text-fg-4"
                title={c.blockReason}
              >
                {c.blockReason ?? "表现未达标"}
              </button>
            )}
            <button className="cursor-pointer rounded-[9px] border border-line bg-transparent px-3.5 py-[9px] text-xs text-fg-3">
              终止
            </button>
            <span className="ml-auto font-mono text-micro text-fg-4">上线需人工批准</span>
          </div>
        </>
      )}
    </Card>
  );
}

export default function Lab() {
  const [candidates, setCandidates] = useState<LabCandidate[]>([]);
  const [history, setHistory] = useState<LabHistoryItem[]>([]);

  useEffect(() => {
    labApi.candidates().then(setCandidates).catch(() => {});
    labApi.history().then(setHistory).catch(() => {});
  }, []);

  return (
    <PageShell title="策略实验室" sub="STRATEGY LAB">
      <div className="mx-auto flex max-w-[1100px] flex-col gap-5">
        {/* 说明条 + 流水线 */}
        <Card>
          <div className="flex items-start gap-3.5">
            <div className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[9px] bg-violet-soft">
              <FlaskConical size={17} className="text-violet" />
            </div>
            <div className="flex-1">
              <div className="mb-1 text-sm font-bold text-fg-1">受控进化 · Shadow Mode</div>
              <div className="text-xs leading-relaxed text-fg-3">
                AI 或人工提出的策略改进不会直接上线。候选版本先以
                <b className="text-violet">影子模式</b>
                并行运行（收到同样的市场数据、产生模拟决策但不下单），与线上版本逐笔对比。影子期 ≥14
                天且关键指标优于基线，方可申请
                <b className="text-amber">灰度</b>
                （小仓位真实运行），最终<b className="text-mint">人工批准</b>
                上线。灰度期回撤超限自动回滚。
              </div>
              {/* 流水线图示 */}
              <div className="mt-3 flex max-w-[560px] items-center">
                {(
                  [
                    ["提案", "var(--ap-fg-3)"],
                    ["SHADOW 14d", "var(--ap-violet)"],
                    ["CANARY 灰度", "var(--ap-amber)"],
                    ["人工批准", "var(--ap-fg-2)"],
                    ["LIVE", "var(--ap-mint)"],
                  ] as const
                ).map(([l, c], i, arr) => (
                  <div key={l} className="contents">
                    <div
                      className="whitespace-nowrap rounded-pill border px-3 py-[5px] font-mono text-[10.5px] font-semibold"
                      style={{ borderColor: c, color: c }}
                    >
                      {l}
                    </div>
                    {i < arr.length - 1 && (
                      <div className="h-[1.5px] min-w-3 flex-1 bg-line" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* 候选 + 历史 */}
        <div className="grid items-start gap-5 min-[1000px]:grid-cols-2">
          {candidates.map((c) => (
            <CandidateCard key={c.id} c={c} />
          ))}

          <Card title="进化历史">
            {history.map((h, i) => (
              <div
                key={h.ts + h.title}
                className={`flex gap-3 py-2.5 ${i < history.length - 1 ? "border-b border-line-soft" : ""}`}
              >
                <div
                  className={`flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full ${
                    h.kind === "promote"
                      ? "bg-mint-soft"
                      : h.kind === "rollback"
                        ? "bg-rose-soft"
                        : "bg-bg-3"
                  }`}
                >
                  {h.kind === "promote" ? (
                    <ArrowUp size={12} strokeWidth={2.2} className="text-mint" />
                  ) : h.kind === "rollback" ? (
                    <ArrowDown size={12} strokeWidth={2.2} className="text-rose" />
                  ) : (
                    <Pause size={12} strokeWidth={2.2} className="text-fg-4" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-fg-1">{h.title}</span>
                    <Pill tone={h.kind === "promote" ? "mint" : h.kind === "rollback" ? "rose" : "default"}>
                      {h.kind === "promote" ? "上线" : h.kind === "rollback" ? "自动回滚" : "退役"}
                    </Pill>
                  </div>
                  <div className="mt-0.5 font-mono text-xs text-fg-4">
                    {h.ts}
                    {h.note ? ` · ${h.note}` : ""}
                  </div>
                </div>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </PageShell>
  );
}
