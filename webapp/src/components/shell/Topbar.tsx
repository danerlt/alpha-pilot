import { Bell, BrainCircuit, Search } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { fmtPct } from "@/lib/format";
import { Dot } from "@/components/ui/atoms";

const RISK_CFG = {
  OK: { color: "var(--ap-mint)", label: "风控正常", cls: "text-mint" },
  WARN: { color: "var(--ap-amber)", label: "接近阈值", cls: "text-amber" },
  HALTED: { color: "var(--ap-rose)", label: "已熔断", cls: "text-rose" },
} as const;

export function Topbar({
  title,
  sub,
  onCommand,
  onChat,
}: {
  title: string;
  sub: string;
  onCommand: () => void;
  onChat: () => void;
}) {
  const { risk } = useApp();
  const cfg = RISK_CFG[risk?.state ?? "OK"];
  return (
    <header className="box-border flex h-[60px] items-center gap-4 border-b border-line-soft bg-bg-1 px-6 py-3.5">
      <div className="min-w-0 flex-1">
        <div className="mb-px text-micro font-medium uppercase tracking-[.08em] text-fg-3">
          {sub}
        </div>
        <div className="text-[16px] font-semibold tracking-[-.01em] text-fg-1">
          {title}
        </div>
      </div>

      {/* 风控状态胶囊 */}
      <div className="flex items-center gap-2.5 rounded-pill border border-line-soft bg-bg-2 px-3 py-1.5">
        <Dot color={cfg.color} glow />
        <span className={`text-xs font-semibold ${cfg.cls}`}>{cfg.label}</span>
        {risk && (
          <span className="whitespace-nowrap font-mono text-xs text-fg-3">
            仓位 {risk.positionsPct}% · 日损 {fmtPct(risk.dayLossPct)} ·{" "}
            {risk.regime}
          </span>
        )}
      </div>

      {/* ⌘K */}
      <button
        onClick={onCommand}
        className="flex w-[260px] cursor-pointer items-center gap-2 rounded-sm border border-line-soft bg-bg-2 py-1.5 pl-3 pr-2.5 text-left hover:border-line"
      >
        <Search size={14} className="text-fg-3" />
        <span className="flex-1 text-xs text-fg-4">
          搜索交易对、决策、策略…
        </span>
        <span className="rounded-[4px] border border-line bg-bg-3 px-1.5 py-0.5 font-mono text-micro text-fg-4">
          Ctrl K
        </span>
      </button>

      {/* Pilot AI */}
      <button
        onClick={onChat}
        title="Pilot AI"
        className="flex cursor-pointer items-center gap-[7px] rounded-sm border border-violet/35 bg-violet-soft px-3 py-[7px] text-violet transition-all hover:brightness-110"
      >
        <BrainCircuit size={14} />
        <span className="text-xs font-semibold">Pilot AI</span>
      </button>

      {/* 通知 */}
      <button className="relative flex h-[34px] w-[34px] cursor-pointer items-center justify-center rounded-sm border border-line-soft bg-bg-2 text-fg-2 hover:text-fg-1">
        <Bell size={15} />
        <span
          className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-rose"
          style={{ boxShadow: "0 0 4px var(--ap-rose)" }}
        />
      </button>

      {/* AUTO 开关态 */}
      <div className="flex items-center gap-2 rounded-sm border border-mint/25 bg-mint-soft px-3 py-1.5">
        <Dot color="var(--ap-mint)" glow />
        <span className="font-mono text-xs font-semibold text-mint">AUTO</span>
      </div>
    </header>
  );
}
