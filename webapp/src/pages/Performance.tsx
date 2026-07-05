/**
 * 回测与绩效（handoff/02 P6）—— 6 指标磁贴 + 策略 vs HODL 曲线 + 月度 PnL 零轴柱图
 * + 交易统计 + 归因维度切换。
 */
import { useState } from "react";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Dot, Stat } from "@/components/ui/atoms";
import {
  useAttribution,
  usePerformanceMonthly,
  usePerformanceSummary,
} from "@/api/queries";
import type {
  AttributionDim,
  MonthlyPnl,
  PerformanceSummary,
} from "@/api/types";
import { fmtPct, fmtSigned } from "@/lib/format";

const DIMS: { k: AttributionDim; l: string }[] = [
  { k: "symbol", l: "按币种" },
  { k: "strategy", l: "按策略" },
  { k: "trigger", l: "按触发类型" },
];

function CompareCurve({ summary }: { summary: PerformanceSummary }) {
  const W = 1000;
  const H = 240;
  const all = summary.curve.flatMap((c) => [c.strategy, c.hodl]);
  const min = Math.min(...all);
  const max = Math.max(...all);
  const r = max - min || 1;
  const px = (i: number) => (i / (summary.curve.length - 1)) * W;
  const py = (v: number) => H - 20 - ((v - min) / r) * (H - 40);
  const path = (key: "strategy" | "hodl") =>
    summary.curve
      .map((c, i) => (i ? "L" : "M") + px(i).toFixed(1) + " " + py(c[key]).toFixed(1))
      .join(" ");
  const stratPath = path("strategy");
  return (
    <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="block">
      <defs>
        <linearGradient id="perf-mint" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="var(--ap-mint)" stopOpacity=".3" />
          <stop offset="1" stopColor="var(--ap-mint)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 1, 2, 3, 4].map((i) => (
        <line key={i} x1="0" x2={W} y1={i * (H / 4)} y2={i * (H / 4)} stroke="var(--ap-line)" strokeOpacity=".4" />
      ))}
      <path d={`${stratPath} L ${W} ${H} L 0 ${H} Z`} fill="url(#perf-mint)" />
      <path d={stratPath} stroke="var(--ap-mint)" strokeWidth="2" fill="none" vectorEffect="non-scaling-stroke" />
      <path d={path("hodl")} stroke="var(--ap-fg-4)" strokeWidth="1.5" fill="none" strokeDasharray="4,3" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function MonthlyBars({ data }: { data: MonthlyPnl[] }) {
  const H = 170;
  const zero = 100;
  const maxV = Math.max(...data.map((d) => Math.abs(d.pnl)), 1);
  const scale = (zero - 30) / maxV;
  return (
    <div className="flex items-stretch gap-2 py-1.5" style={{ height: H }}>
      {data.map((d) => {
        const pos = d.pnl >= 0;
        const barH = Math.max(3, Math.abs(d.pnl) * scale);
        return (
          <div key={d.month} className="relative flex-1">
            <div className="absolute left-0 right-0 h-px bg-line opacity-60" style={{ top: zero }} />
            <div
              className={`absolute rounded-[3px] ${pos ? "bg-mint" : "bg-rose"}`}
              style={{
                left: "8%",
                right: "8%",
                opacity: 0.88,
                top: pos ? zero - barH : zero + 1,
                height: barH,
              }}
            />
            <div
              className={`absolute left-0 right-0 text-center font-mono text-micro ${pos ? "text-mint" : "text-rose"}`}
              style={{ top: pos ? zero - barH - 16 : zero + barH + 4 }}
            >
              {pos ? "+" : ""}
              {(d.pnl / 1000).toFixed(1)}k
            </div>
            <div className="absolute bottom-0 left-0 right-0 text-center font-mono text-[9px] text-fg-4">
              {d.month}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function Performance() {
  const [dim, setDim] = useState<AttributionDim>("symbol");
  const { data: summary } = usePerformanceSummary();
  const { data: monthly = [] } = usePerformanceMonthly();
  const { data: rows = [] } = useAttribution(dim);

  return (
    <PageShell title="回测与绩效" sub="PERFORMANCE">
      <div className="flex flex-col gap-5">
        {summary && (
          <div className="grid grid-cols-2 gap-3 min-[900px]:grid-cols-3 min-[1280px]:grid-cols-6">
            <Card dense>
              <Stat label="净收益" value={fmtPct(summary.netReturnPct)} tone="pos" sub={`vs ${fmtPct(summary.hodlBtcReturnPct)} HODL`} />
            </Card>
            <Card dense>
              <Stat label="Sharpe" value={summary.sharpe.toFixed(2)} sub="risk-adjusted" />
            </Card>
            <Card dense>
              <Stat label="Sortino" value={summary.sortino.toFixed(2)} sub="下行风险" />
            </Card>
            <Card dense>
              <Stat label="最大回撤" value={fmtPct(summary.maxDD)} tone="neg" />
            </Card>
            <Card dense>
              <Stat label="胜率" value={`${summary.winRate}%`} sub="已平仓口径" />
            </Card>
            <Card dense>
              <Stat label="盈亏比" value={`${summary.profitFactor.toFixed(1)}:1`} sub="avg R:R" />
            </Card>
          </div>
        )}

        {summary && (
          <Card
            title="策略收益对比 (90 天)"
            right={
              <div className="flex gap-3 font-mono text-xs">
                <span className="flex items-center gap-1.5">
                  <Dot color="var(--ap-mint)" glow />
                  <span className="text-fg-1">AlphaPilot</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <Dot color="var(--ap-fg-4)" />
                  <span className="text-fg-3">BTC HODL</span>
                </span>
              </div>
            }
          >
            <div className="relative -mx-[18px] -mb-4">
              <CompareCurve summary={summary} />
            </div>
          </Card>
        )}

        <div className="grid gap-5 min-[1100px]:grid-cols-[2fr_1fr]">
          <Card title="月度 PnL 分布">
            {monthly.length > 0 && <MonthlyBars data={monthly} />}
          </Card>

          <Card title="交易统计">
            {(
              [
                ["总交易数", "85"],
                ["盈利笔数", "48"],
                ["亏损笔数", "37"],
                ["平均盈利", "+$124.80"],
                ["平均亏损", "−$54.30"],
                ["最大连续盈利", "8 笔"],
                ["最大连续亏损", "3 笔"],
                ["平均持仓", "2h 14m"],
              ] as const
            ).map(([l, v], i, a) => (
              <div
                key={l}
                className={`flex justify-between py-2 text-xs ${i < a.length - 1 ? "border-b border-line-soft" : ""}`}
              >
                <span className="text-fg-3">{l}</span>
                <span className="font-mono font-semibold text-fg-1">{v}</span>
              </div>
            ))}
          </Card>
        </div>

        {/* 归因切换 */}
        <Card
          title="盈亏归因"
          right={
            <div className="flex gap-1 rounded-sm bg-bg-3 p-[3px]">
              {DIMS.map((d) => (
                <button
                  key={d.k}
                  onClick={() => setDim(d.k)}
                  className={`cursor-pointer rounded-[5px] px-2.5 py-1 text-xs ${
                    dim === d.k ? "bg-bg-4 text-fg-1" : "text-fg-3"
                  }`}
                >
                  {d.l}
                </button>
              ))}
            </div>
          }
        >
          <div className="-mx-[18px] -my-4 overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="border-b border-line">
                  {["维度", "交易数", "净盈亏", "胜率", "占比"].map((h) => (
                    <th key={h} className="px-3.5 py-2.5 text-left text-micro font-medium uppercase tracking-[.06em] text-fg-3">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const total = rows.reduce((s, x) => s + Math.abs(x.pnl), 0) || 1;
                  return (
                    <tr key={r.key} className="border-b border-line-soft">
                      <td className="px-3.5 py-3 font-medium text-fg-1">{r.key}</td>
                      <td className="px-3.5 py-3 font-mono text-fg-2">{r.trades}</td>
                      <td className={`px-3.5 py-3 font-mono font-semibold ${r.pnl >= 0 ? "text-mint" : "text-rose"}`}>
                        {fmtSigned(r.pnl)}
                      </td>
                      <td className="px-3.5 py-3 font-mono text-fg-2">{r.winRate}%</td>
                      <td className="px-3.5 py-3">
                        <div className="h-1.5 w-full max-w-[160px] overflow-hidden rounded-[3px] bg-bg-3">
                          <div
                            className={`h-full rounded-[3px] ${r.pnl >= 0 ? "bg-mint" : "bg-rose"}`}
                            style={{ width: `${(Math.abs(r.pnl) / total) * 100}%`, opacity: 0.85 }}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
