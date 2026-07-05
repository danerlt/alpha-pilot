/**
 * 策略与风控（handoff/02 P7）—— 受限策略集（启停开关）+ 硬风控表（只读 + 修改走确认）
 * + 交易对管理。
 */
import { useState } from "react";
import { AlertTriangle, Plus } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Dot, Pill } from "@/components/ui/atoms";
import { Switch } from "@/components/ui/form";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { CoinAvatar } from "@/components/positions/PositionsTable";
import { useHardLimits, useStrategies, useSymbolConfigs } from "@/api/queries";
import { qk } from "@/api/queryClient";
import { strategyApi } from "@/api/services";
import type { StrategyCard } from "@/api/types";

export default function Risk() {
  const queryClient = useQueryClient();
  const { data: strategies = [] } = useStrategies();
  const { data: limits = [] } = useHardLimits();
  const { data: symbols = [] } = useSymbolConfigs();
  const [toggling, setToggling] = useState<StrategyCard | null>(null);
  const [busy, setBusy] = useState(false);

  const doToggle = async () => {
    if (!toggling) return;
    setBusy(true);
    try {
      await strategyApi.toggle(toggling.id, !toggling.enabled);
      await queryClient.invalidateQueries({ queryKey: qk.strategies });
      setToggling(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageShell title="策略与风控" sub="RISK & STRATEGY">
      <div className="grid gap-5 min-[1100px]:grid-cols-2">
        {/* 策略受限集 */}
        <Card title="策略框架 · 受限集">
          <div className="flex flex-col gap-3">
            {strategies.map((s) => (
              <div
                key={s.id}
                className={`rounded-[10px] border bg-bg-3 p-3.5 ${
                  s.enabled ? "border-mint" : "border-line-soft"
                }`}
              >
                <div className="mb-1.5 flex items-center gap-2.5">
                  <Dot color={s.enabled ? "var(--ap-mint)" : "var(--ap-fg-4)"} glow={s.enabled} />
                  <span className="text-sm font-semibold text-fg-1">{s.name}</span>
                  {s.enabled && <Pill tone="mint">ACTIVE</Pill>}
                  <div className="ml-auto">
                    <Switch on={s.enabled} onToggle={() => setToggling(s)} />
                  </div>
                </div>
                <div className="mb-2 text-xs text-fg-3">{s.desc}</div>
                <div className="flex gap-1.5">
                  {s.regimes.map((r) => (
                    <Pill key={r}>{r}</Pill>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* 硬风控 */}
        <Card title="硬风控 · 不可 AI 学习">
          <div className="mb-3.5 flex items-start gap-2 rounded-sm border border-amber/20 bg-amber-soft px-3 py-2.5">
            <AlertTriangle size={14} className="mt-px shrink-0 text-amber" />
            <span className="text-xs leading-normal text-fg-2">
              硬风控阈值为系统级保护，AI 不可绕过或自我修改，所有决策必须通过守卫检查。修改需 admin 权限并记录审计日志。
            </span>
          </div>
          {limits.map((r, i) => (
            <div
              key={r.key}
              className={`flex items-center py-2.5 ${i < limits.length - 1 ? "border-b border-line-soft" : ""}`}
            >
              <div className="flex-1">
                <div className="text-sm text-fg-2">{r.label}</div>
                <div className="mt-0.5 text-micro text-fg-4">{r.desc}</div>
              </div>
              <span
                className={`mr-2 font-mono text-sm font-semibold ${
                  r.label.includes("亏损") ? "text-rose" : "text-fg-1"
                }`}
              >
                {r.value}
              </span>
              <span className="font-mono text-micro text-fg-4">{r.key}</span>
            </div>
          ))}
        </Card>

        {/* 交易对管理 */}
        <Card title="交易对" className="min-[1100px]:col-span-2">
          <div className="flex flex-wrap gap-2.5">
            {symbols.map((p) => (
              <div
                key={p.symbol}
                className={`flex min-w-[180px] items-center gap-2.5 rounded-[10px] border bg-bg-3 px-3.5 py-2.5 ${
                  p.enabled ? "border-mint" : "border-line-soft"
                }`}
              >
                <CoinAvatar symbol={p.symbol} size={28} />
                <div className="flex-1">
                  <div className="font-mono text-xs font-semibold text-fg-1">{p.symbol}</div>
                  <div className="font-mono text-micro text-fg-3">
                    仓位上限 {p.maxPositionPct}%
                  </div>
                </div>
                <Pill tone={p.enabled ? "mint" : "default"}>{p.enabled ? "ON" : "OFF"}</Pill>
              </div>
            ))}
            <button className="flex cursor-pointer items-center gap-2 rounded-[10px] border-[1.5px] border-dashed border-line bg-transparent px-3.5 py-2.5 text-xs text-fg-3 hover:text-fg-2">
              <Plus size={13} /> 添加交易对
            </button>
          </div>
        </Card>
      </div>

      {/* 策略启停确认 */}
      <ConfirmDialog
        open={toggling !== null}
        onClose={() => setToggling(null)}
        onConfirm={doToggle}
        busy={busy}
        title={toggling ? `${toggling.enabled ? "停用" : "启用"}策略 · ${toggling.name}` : ""}
        confirmLabel={toggling?.enabled ? "确认停用" : "确认启用"}
        body={
          toggling && (
            <>
              {toggling.enabled ? (
                <>
                  停用后 AI 将不再基于 <b className="text-fg-1">{toggling.name}</b>{" "}
                  产生新决策，已有持仓的止损止盈监控不受影响。
                </>
              ) : (
                <>
                  启用后 <b className="text-fg-1">{toggling.name}</b>{" "}
                  将参与决策产生。适用 regime：
                  <span className="font-mono">{toggling.regimes.join(" / ")}</span>。
                </>
              )}
              该操作将记录审计日志。
            </>
          )
        }
      />
    </PageShell>
  );
}
