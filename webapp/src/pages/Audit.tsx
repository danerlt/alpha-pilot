/**
 * 审计日志（handoff/02 P9）—— 事件流全量 + 类型过滤 + AI 日报卡。
 */
import { useMemo, useState } from "react";
import { PageShell } from "@/components/shell/PageShell";
import { Card } from "@/components/ui/atoms";
import { EventRow } from "@/components/events/EventRow";
import { useEvents, useReports } from "@/api/queries";
import type { EventKind } from "@/api/types";
import { fmtSigned } from "@/lib/format";

type Filter = "all" | EventKind;

const FILTERS: { k: Filter; l: string }[] = [
  { k: "all", l: "全部" },
  { k: "ai", l: "AI" },
  { k: "guard", l: "守卫" },
  { k: "fill", l: "成交" },
  { k: "breaker", l: "熔断" },
];

export default function Audit() {
  const { data: events = [] } = useEvents();
  const { data: reports = [] } = useReports();
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = useMemo(
    () => events.filter((e) => filter === "all" || e.kind === filter),
    [events, filter],
  );

  return (
    <PageShell title="审计日志" sub="AUDIT LOG">
      <div className="mx-auto flex max-w-[1100px] flex-col gap-4">
        <Card
          title="事件流 · 今日"
          right={
            <div className="flex gap-1.5">
              {FILTERS.map((f) => (
                <button
                  key={f.k}
                  onClick={() => setFilter(f.k)}
                  className={`cursor-pointer rounded-xs border border-line-soft px-2.5 py-1 text-xs ${
                    filter === f.k ? "bg-bg-4 text-fg-1" : "bg-bg-3 text-fg-3"
                  }`}
                >
                  {f.l}
                </button>
              ))}
            </div>
          }
        >
          <div className="flex flex-col">
            {filtered.map((e) => (
              <EventRow key={e.id} e={e} />
            ))}
            {filtered.length === 0 && (
              <div className="py-8 text-center text-sm text-fg-4">
                该类型下暂无事件
              </div>
            )}
          </div>
        </Card>

        {reports.map((r) => (
          <Card key={r.id} title={`AI 日报 · ${r.date}`}>
            <div className="mb-3 flex gap-4 font-mono text-xs text-fg-3">
              <span>
                交易 <b className="text-fg-1">{r.trades} 笔</b>
              </span>
              <span>
                净收益{" "}
                <b className={r.pnl >= 0 ? "text-mint" : "text-rose"}>
                  {fmtSigned(r.pnl)}
                </b>
              </span>
            </div>
            <div className="text-sm leading-[1.7] text-fg-2">{r.narrative}</div>
          </Card>
        ))}
      </div>
    </PageShell>
  );
}
