/**
 * AI 决策流（handoff/02 P4）—— 过滤 tab（全部/已执行/已拦截）+ 决策卡列表（首条流式重放）
 * + 卡片点击详情（features 快照/守卫逐项/reasoning 全文/关联订单）。
 */
import { useEffect, useMemo, useState } from "react";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Dot, Pill } from "@/components/ui/atoms";
import { Modal } from "@/components/ui/Modal";
import { DecisionCard } from "@/components/decision/DecisionCard";
import { StreamingDecision } from "@/components/decision/StreamingDecision";
import {
  getVariant,
  setVariant,
  type CardVariant,
} from "@/components/decision/variant";
import { HaltBanner } from "@/components/risk/HaltBanner";
import { useApp } from "@/context/AppContext";
import { decisionsApi, ordersApi } from "@/api/services";
import type { Decision, Order } from "@/api/types";
import { fmt } from "@/lib/format";

type Filter = "all" | "exec" | "blocked";

const VARIANTS: { k: CardVariant; l: string }[] = [
  { k: "stepper", l: "Stepper" },
  { k: "timeline", l: "Timeline" },
  { k: "graph", l: "Graph" },
];

export default function Decisions() {
  const { risk } = useApp();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [variant, setVariantState] = useState<CardVariant>(getVariant());
  const [detail, setDetail] = useState<Decision | null>(null);
  const [relatedOrders, setRelatedOrders] = useState<Order[]>([]);
  const [ackHalt, setAckHalt] = useState(false);

  useEffect(() => {
    decisionsApi.list().then(setDecisions).catch(() => {});
  }, []);

  useEffect(() => {
    if (!detail) return;
    ordersApi
      .list()
      .then((os) =>
        setRelatedOrders(os.filter((o) => o.symbol === detail.symbol).slice(0, 4)),
      )
      .catch(() => {});
  }, [detail]);

  const filtered = useMemo(
    () =>
      decisions.filter(
        (d) =>
          filter === "all" ||
          (filter === "exec" && d.guard === "PASS") ||
          (filter === "blocked" && d.guard !== "PASS"),
      ),
    [decisions, filter],
  );

  const tabs: { k: Filter; l: string; n: number }[] = [
    { k: "all", l: "全部", n: decisions.length },
    { k: "exec", l: "已执行", n: decisions.filter((d) => d.guard === "PASS").length },
    { k: "blocked", l: "已拦截", n: decisions.filter((d) => d.guard !== "PASS").length },
  ];

  const pickVariant = (v: CardVariant) => {
    setVariant(v);
    setVariantState(v);
  };

  return (
    <PageShell title="AI 决策流" sub="AI DECISIONS">
      <div className="mx-auto flex max-w-[1100px] flex-col gap-4">
        {risk && !ackHalt && <HaltBanner risk={risk} onAck={() => setAckHalt(true)} />}

        <div className="flex flex-wrap items-center gap-2">
          {tabs.map((t) => (
            <button
              key={t.k}
              onClick={() => setFilter(t.k)}
              className={`inline-flex shrink-0 cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-sm border px-3.5 py-1.5 text-xs font-medium ${
                filter === t.k
                  ? "border-line bg-bg-3 text-fg-1"
                  : "border-line-soft bg-bg-2 text-fg-3"
              }`}
            >
              {t.l} <span className="font-mono text-micro opacity-70">{t.n}</span>
            </button>
          ))}
          <div className="ml-auto flex items-center gap-1.5">
            <span className="font-mono text-xs text-fg-3">卡片样式</span>
            <div className="inline-flex rounded-sm border border-line bg-bg-3 p-[3px]">
              {VARIANTS.map((v) => (
                <button
                  key={v.k}
                  onClick={() => pickVariant(v.k)}
                  className={`cursor-pointer rounded-[5px] px-2.5 py-1 font-mono text-xs ${
                    variant === v.k ? "bg-bg-4 text-violet" : "text-fg-3"
                  }`}
                >
                  {v.l}
                </button>
              ))}
            </div>
          </div>
        </div>

        {filtered.map((d, i) => (
          <div
            key={d.id}
            onClick={() => setDetail(d)}
            className="cursor-pointer text-left"
          >
            {i === 0 ? (
              <StreamingDecision d={d} variant={variant} />
            ) : (
              <DecisionCard d={d} variant={variant} />
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <Card>
            <div className="py-10 text-center text-sm text-fg-4">
              该条件下暂无决策记录
            </div>
          </Card>
        )}
      </div>

      {/* 决策详情 */}
      <Modal
        open={detail !== null}
        onClose={() => setDetail(null)}
        title={
          detail ? (
            <span className="font-mono">
              {detail.id} · {detail.symbol} · {detail.action}
            </span>
          ) : (
            ""
          )
        }
        width={640}
      >
        {detail && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <Pill
                tone={
                  detail.guard === "PASS"
                    ? "mint"
                    : detail.guard === "REJECT"
                      ? "rose"
                      : "amber"
                }
              >
                守卫 {detail.guard}
              </Pill>
              <Pill tone="violet">conf {detail.confidence.toFixed(2)}</Pill>
              <Pill>{detail.strategy}</Pill>
              <span className="ml-auto font-mono text-xs text-fg-4">{detail.ts}</span>
            </div>

            {detail.features && (
              <div>
                <div className="mb-2 text-micro font-semibold uppercase tracking-[.08em] text-fg-3">
                  Features 快照
                </div>
                <div className="grid grid-cols-2 gap-1.5 min-[520px]:grid-cols-3">
                  {detail.features.map((f) => (
                    <div
                      key={f.k}
                      className="flex justify-between gap-2 rounded-xs border border-line-soft bg-bg-3 px-2.5 py-1.5 font-mono text-xs"
                    >
                      <span className="text-fg-3">{f.k}</span>
                      <span className="text-cyan">{f.v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {detail.guards && (
              <div>
                <div className="mb-2 text-micro font-semibold uppercase tracking-[.08em] text-fg-3">
                  守卫逐项结果
                </div>
                <div className="flex flex-col gap-1">
                  {detail.guards.map((g) => (
                    <div
                      key={g.k}
                      className="flex items-center gap-2 rounded-xs border border-line-soft bg-bg-3 px-2.5 py-1.5 font-mono text-xs"
                    >
                      <Dot color={g.ok ? "var(--ap-mint)" : "var(--ap-rose)"} />
                      <span className="flex-1 text-fg-2">{g.k}</span>
                      <span className={g.ok ? "text-fg-3" : "text-rose"}>{g.note}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <div className="mb-2 text-micro font-semibold uppercase tracking-[.08em] text-violet">
                Reasoning 全文
              </div>
              <div className="rounded-sm bg-bg-3 px-3.5 py-3 text-sm leading-relaxed text-fg-2">
                {detail.reason}
              </div>
            </div>

            {relatedOrders.length > 0 && (
              <div>
                <div className="mb-2 text-micro font-semibold uppercase tracking-[.08em] text-fg-3">
                  关联订单
                </div>
                <div className="flex flex-col gap-1">
                  {relatedOrders.map((o) => (
                    <div
                      key={o.id}
                      className="flex items-center gap-2.5 rounded-xs border border-line-soft bg-bg-3 px-2.5 py-1.5 font-mono text-xs"
                    >
                      <span className="text-fg-4">{o.ts}</span>
                      <Pill tone={o.side === "BUY" ? "mint" : "rose"}>{o.side}</Pill>
                      <span className="text-fg-2">{o.type}</span>
                      <span className="ml-auto text-fg-1">
                        {o.qty} @ {fmt(o.price)}
                      </span>
                      <Pill
                        tone={
                          o.status === "FILLED"
                            ? "mint"
                            : o.status === "WORKING"
                              ? "cyan"
                              : "default"
                        }
                      >
                        {o.status}
                      </Pill>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </PageShell>
  );
}
