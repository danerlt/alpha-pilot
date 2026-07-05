/**
 * 主控制台（handoff/02 P2）—— 左主列（AI hero / 权益 / 磁贴 / 持仓）+ 右事件流。
 * HALTED 场景五件套联动：横幅 / hero 被拒 / 曲线变 rose / 事件流红条 / 顶栏胶囊（Topbar 内）。
 */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Pill, Stat } from "@/components/ui/atoms";
import { StreamingDecision } from "@/components/decision/StreamingDecision";
import { getVariant } from "@/components/decision/variant";
import { HaltBanner } from "@/components/risk/HaltBanner";
import { AnimatedNumber } from "@/components/charts/AnimatedNumber";
import { SparkLive } from "@/components/charts/SparkLive";
import { PositionsTable } from "@/components/positions/PositionsTable";
import { EventRow } from "@/components/events/EventRow";
import { useApp } from "@/context/AppContext";
import { stream } from "@/api/stream";
import {
  accountApi,
  decisionsApi,
  eventsApi,
  positionsApi,
} from "@/api/services";
import type {
  AccountSnapshot,
  Decision,
  EventItem,
  Position,
} from "@/api/types";
import { fmt, fmtPct, fmtSigned } from "@/lib/format";

const RANGES = ["1D", "1W", "1M", "3M", "ALL"] as const;

export default function Dashboard() {
  const { risk, account, setScene } = useApp();
  const navigate = useNavigate();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [equitySeries, setEquitySeries] = useState<AccountSnapshot[]>([]);
  const [range, setRange] = useState<(typeof RANGES)[number]>("1M");
  const [ackHalt, setAckHalt] = useState(false);
  const variant = getVariant();

  useEffect(() => {
    decisionsApi.list().then(setDecisions).catch(() => {});
    positionsApi.list().then(setPositions).catch(() => {});
    eventsApi.recent().then(setEvents).catch(() => {});
    accountApi.history().then(setEquitySeries).catch(() => {});
  }, []);

  // 实时驱动：事件流追加 / 新决策置顶（触发流式重放）/ 权益曲线生长
  useEffect(() => {
    const offEvent = stream.subscribe("event.append", (e) =>
      setEvents((prev) => [e, ...prev].slice(0, 60)),
    );
    const offDecision = stream.subscribe("decision.complete", (d) =>
      setDecisions((prev) => [d, ...prev].slice(0, 20)),
    );
    const offSnap = stream.subscribe("account.snapshot", (s) =>
      setEquitySeries((prev) => [...prev, s].slice(-120)),
    );
    return () => {
      offEvent();
      offDecision();
      offSnap();
    };
  }, []);

  const halted = risk?.state === "HALTED";

  // 风控状态变化时重置横幅关闭态（再次 WARN/HALTED 要重新出现）
  useEffect(() => {
    setAckHalt(false);
  }, [risk?.state]);

  // HALTED 时 hero 决策显示被拒（设计稿 pages.jsx 同款处理）
  const heroDecision = useMemo<Decision | null>(() => {
    if (decisions.length === 0) return null;
    if (!halted) return decisions[0];
    return {
      ...decisions[0],
      action: "HOLD",
      guard: "REJECT",
      confidence: 0.31,
      strategy: "熔断保护",
      reason:
        "日亏损达到熔断阈值，守卫拒绝所有新开仓，仅允许平仓与风险管理操作。",
      sl: undefined,
    };
  }, [decisions, halted]);

  return (
    <PageShell title="主控制台" sub="COCKPIT">
      {risk && !ackHalt && (
        <HaltBanner
          risk={risk}
          onAck={() => setAckHalt(true)}
          onResolve={() => setScene("ok")}
        />
      )}
      <div className="grid gap-5 min-[1180px]:grid-cols-[minmax(0,1fr)_360px]">
        {/* 左主列 */}
        <div className="flex min-w-0 flex-col gap-5">
          {/* AI hero */}
          {heroDecision && (
            <StreamingDecision d={heroDecision} variant={variant} />
          )}

          {/* 权益卡 */}
          <Card
            title="账户权益"
            right={
              <div className="flex gap-1 rounded-sm bg-bg-3 p-[3px]">
                {RANGES.map((r) => (
                  <button
                    key={r}
                    onClick={() => setRange(r)}
                    className={`cursor-pointer rounded-[5px] px-2.5 py-1 font-mono text-xs ${
                      range === r ? "bg-bg-4 text-fg-1" : "text-fg-3"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            }
          >
            <div className="mb-4 grid grid-cols-2 gap-6 min-[900px]:grid-cols-4">
              <div className="flex flex-col gap-1">
                <div className="text-[10.5px] font-medium uppercase tracking-[.08em] text-fg-3">
                  当前权益
                </div>
                <AnimatedNumber
                  value={account?.equity ?? 0}
                  prefix="$"
                  format={(v) => fmt(v)}
                  className="text-[28px] font-bold leading-[1.1] tracking-[-.02em] text-fg-1"
                />
                {account && (
                  <div className="font-mono text-[11.5px] text-fg-3">
                    {fmtSigned(account.equityChange)} 今日
                  </div>
                )}
              </div>
              {account && (
                <>
                  <Stat
                    label="今日"
                    value={fmtPct(account.todayPnlPct)}
                    sub={fmtSigned(account.todayPnl)}
                    tone={account.todayPnl >= 0 ? "pos" : "neg"}
                  />
                  <Stat
                    label="本周"
                    value={fmtPct(account.weekPnlPct)}
                    sub={fmtSigned(account.weekPnl)}
                    tone={account.weekPnl >= 0 ? "pos" : "neg"}
                  />
                  <Stat
                    label="本月"
                    value={fmtPct(account.mtdPnlPct)}
                    sub={fmtSigned(account.mtdPnl)}
                    tone={account.mtdPnl >= 0 ? "pos" : "neg"}
                  />
                </>
              )}
            </div>
            <div className="relative -mx-[18px] -mb-4">
              <SparkLive
                data={equitySeries.map((s) => s.equity)}
                h={160}
                color={halted ? "var(--ap-rose)" : "var(--ap-mint)"}
              />
            </div>
          </Card>

          {/* 指标磁贴 ×4 */}
          {account && (
            <div className="grid grid-cols-2 gap-3 min-[900px]:grid-cols-4">
              <Card dense>
                <Stat label="今日交易" value={account.tradesToday} sub={`胜率 ${account.winRate}%`} />
              </Card>
              <Card dense>
                <Stat label="Sharpe 30d" value={account.sharpe.toFixed(2)} sub="risk-adjusted" />
              </Card>
              <Card dense>
                <Stat label="最大回撤" value={fmtPct(account.maxDD)} sub="阈值 −8%" tone="neg" />
              </Card>
              <Card dense>
                <Stat label="平均持仓时长" value={account.avgHold} sub="中短线" />
              </Card>
            </div>
          )}

          {/* 持仓预览 */}
          <Card
            title="当前持仓"
            right={
              <button
                onClick={() => navigate("/positions")}
                className="cursor-pointer font-mono text-xs text-mint"
              >
                查看全部 →
              </button>
            }
          >
            {positions.length > 0 ? (
              <PositionsTable
                positions={positions}
                onRowClick={() => navigate("/positions")}
              />
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center">
                <div className="text-sm font-semibold text-fg-2">暂无持仓</div>
                <div className="text-xs text-fg-4">AI 正在等待入场信号</div>
              </div>
            )}
          </Card>
        </div>

        {/* 右列：事件流 */}
        <Card
          title="事件流 · 实时"
          right={<Pill tone="mint">LIVE</Pill>}
          className="h-fit min-[1180px]:sticky min-[1180px]:top-0"
        >
          <div className="flex max-h-[780px] flex-col overflow-auto">
            {halted && (
              <div className="-mx-1 flex gap-2.5 rounded-xs border-b border-line-soft bg-rose-soft px-1.5 py-2.5">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-xs bg-rose">
                  <AlertTriangle size={12} strokeWidth={2.4} style={{ color: "var(--ap-bg-0)" }} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold leading-normal text-rose">
                    熔断触发 · 新开仓已暂停
                  </div>
                  <div className="mt-0.5 font-mono text-micro text-fg-4">
                    {risk ? `日损 ${fmtPct(risk.dayLossPct)}` : ""}
                  </div>
                </div>
              </div>
            )}
            {events.map((e) => (
              <EventRow key={e.id} e={e} />
            ))}
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
