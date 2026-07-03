import { NavLink, useNavigate } from "react-router-dom";
import {
  BarChart3,
  BrainCircuit,
  CandlestickChart,
  FlaskConical,
  Layers,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Settings,
  Shield,
  Users,
} from "lucide-react";
import { useApp } from "@/context/AppContext";
import { fmt, fmtPct } from "@/lib/format";
import { Dot } from "@/components/ui/atoms";

const NAV = [
  { to: "/", label: "主控制台", icon: LayoutDashboard },
  { to: "/market", label: "行情", icon: CandlestickChart },
  { to: "/decisions", label: "AI 决策", icon: BrainCircuit, badge: 5 },
  { to: "/positions", label: "持仓与订单", icon: Layers },
  { to: "/performance", label: "回测与绩效", icon: BarChart3 },
  { to: "/risk", label: "策略与风控", icon: Shield },
  { to: "/lab", label: "策略实验室", icon: FlaskConical, badge: 2 },
  { to: "/audit", label: "审计日志", icon: ScrollText },
  { to: "/admin", label: "后台管理", icon: Users },
  { to: "/settings", label: "设置", icon: Settings },
];

export function Sidebar() {
  const { account } = useApp();
  const navigate = useNavigate();
  return (
    <aside className="flex h-full w-[240px] shrink-0 flex-col border-r border-line bg-bg-1">
      {/* 品牌 */}
      <div className="flex items-center gap-2.5 border-b border-line-soft px-5 pb-6 pt-5">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-sm text-[15px] font-extrabold text-bg-0"
          style={{
            background:
              "linear-gradient(135deg, var(--ap-mint) 0%, var(--ap-violet) 100%)",
          }}
        >
          α
        </div>
        <div>
          <div className="text-[15px] font-bold tracking-[-.01em] text-fg-1">
            Alpha<span className="text-mint">Pilot</span>
          </div>
          <div className="font-mono text-micro tracking-[.05em] text-fg-4">
            v0.1 · testnet
          </div>
        </div>
      </div>

      {/* 账户权益 */}
      <div className="border-b border-line-soft px-5 py-4">
        <div className="mb-1.5 text-micro font-medium uppercase tracking-[.08em] text-fg-3">
          账户权益
        </div>
        <div className="font-mono text-h2 font-bold leading-[1.1] tracking-[-.02em] text-fg-1">
          {account ? `$${fmt(account.equity)}` : "—"}
        </div>
        {account && (
          <div
            className={`mt-1 font-mono text-xs ${account.equityChangePct >= 0 ? "text-mint" : "text-rose"}`}
          >
            {fmtPct(account.equityChangePct)} 今日
          </div>
        )}
      </div>

      {/* 导航 */}
      <nav className="flex flex-1 flex-col gap-px overflow-auto px-3 py-3">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.to === "/"}
            className={({ isActive }) =>
              `relative flex items-center gap-2.5 rounded-sm px-2.5 py-[9px] text-sm font-medium transition-colors duration-150 ${
                isActive
                  ? "bg-bg-3 text-fg-1"
                  : "text-fg-3 hover:bg-bg-2 hover:text-fg-2"
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute -left-3 bottom-2 top-2 w-[3px] rounded-[2px] bg-mint" />
                )}
                <n.icon
                  size={16}
                  className={isActive ? "text-mint" : "text-current"}
                />
                <span className="flex-1">{n.label}</span>
                {n.badge && (
                  <span className="rounded-pill bg-violet-soft px-1.5 py-px font-mono text-micro font-semibold text-violet">
                    {n.badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* 底部：引擎状态 + 用户卡 */}
      <div className="flex flex-col gap-2.5 border-t border-line-soft px-3.5 py-3">
        <div className="flex items-center gap-2">
          <Dot color="var(--ap-mint)" glow pulse />
          <span className="text-xs font-medium text-fg-2">引擎运行中</span>
          <span className="ml-auto font-mono text-micro text-fg-4">48ms</span>
        </div>
        <div className="flex items-center gap-2 rounded-[9px] border border-line-soft bg-bg-2 p-2">
          <div
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold text-fg-1"
            style={{ background: "var(--ap-mint-dim)" }}
          >
            DL
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs font-semibold text-fg-1">
              Daner Li
            </div>
            <div className="font-mono text-[9.5px] font-semibold text-violet">
              OWNER
            </div>
          </div>
          <button
            title="退出登录"
            onClick={() => navigate("/login")}
            className="flex h-[26px] w-[26px] shrink-0 cursor-pointer items-center justify-center rounded-[7px] border border-line-soft bg-transparent text-fg-4 hover:text-fg-1"
          >
            <LogOut size={12} />
          </button>
        </div>
      </div>
    </aside>
  );
}
