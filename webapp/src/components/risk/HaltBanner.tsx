/** 熔断/预警横幅 —— 对齐设计稿 enhancements.jsx HaltBanner */
import { AlertTriangle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { RiskState } from "@/api/types";
import { fmtPct } from "@/lib/format";

export function HaltBanner({
  risk,
  onAck,
  onResolve,
}: {
  risk: RiskState;
  onAck: () => void;
  onResolve?: () => void;
}) {
  const navigate = useNavigate();
  if (risk.state === "OK") return null;
  const halted = risk.state === "HALTED";
  const c = halted ? "var(--ap-rose)" : "var(--ap-amber)";
  return (
    <div
      role="alert"
      className={`relative mb-5 flex items-center gap-3.5 overflow-hidden rounded-md border px-[18px] py-3.5 ${
        halted ? "border-rose bg-rose-soft" : "border-amber bg-amber-soft"
      }`}
      style={halted ? { boxShadow: "0 0 32px rgba(255,77,109,.18)" } : undefined}
    >
      {halted && (
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background: `repeating-linear-gradient(45deg, transparent, transparent 12px, ${c}0a 12px, ${c}0a 24px)`,
          }}
        />
      )}
      <div
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[9px]"
        style={{ background: c, boxShadow: `0 0 16px ${c}66` }}
      >
        <AlertTriangle size={18} strokeWidth={2.4} style={{ color: "var(--ap-bg-0)" }} />
      </div>
      <div className="relative min-w-0 flex-1">
        <div className={`mb-0.5 text-sm font-bold ${halted ? "text-rose" : "text-amber"}`}>
          {halted ? "日亏损熔断已触发 · 新开仓已暂停" : "接近熔断阈值 · 风险升高"}
        </div>
        <div className="font-mono text-xs text-fg-2">
          {halted
            ? `日损 ${fmtPct(risk.dayLossPct)} ≥ 阈值 −2.00% · 仅允许平仓与风险管理 · regime ${risk.regime}`
            : `日损 ${fmtPct(risk.dayLossPct)} · 距阈值 ${Math.abs(-2.0 - risk.dayLossPct).toFixed(2)}% · regime ${risk.regime}`}
        </div>
      </div>
      <div className="relative flex shrink-0 gap-2">
        {halted && (
          <button
            onClick={() => navigate("/audit")}
            className="cursor-pointer rounded-sm border bg-transparent px-3.5 py-2 text-xs font-semibold text-rose"
            style={{ borderColor: c }}
          >
            查看风控日志
          </button>
        )}
        <button
          onClick={halted ? onResolve ?? onAck : onAck}
          className="cursor-pointer rounded-sm border-none px-3.5 py-2 text-xs font-bold"
          style={{ background: c, color: "var(--ap-bg-0)" }}
        >
          {halted ? "手动恢复" : "我知道了"}
        </button>
      </div>
    </div>
  );
}
