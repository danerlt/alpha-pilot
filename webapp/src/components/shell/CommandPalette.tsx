/** ⌘K 命令面板 —— 页面导航 + 交易对搜索（handoff/04 P0 验收项） */
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CandlestickChart, CornerDownLeft, Search } from "lucide-react";
import { mockSymbols } from "@/api/mock/data";

const PAGES = [
  { label: "主控制台", to: "/" },
  { label: "行情", to: "/market" },
  { label: "AI 决策", to: "/decisions" },
  { label: "持仓与订单", to: "/positions" },
  { label: "回测与绩效", to: "/performance" },
  { label: "策略与风控", to: "/risk" },
  { label: "策略实验室", to: "/lab" },
  { label: "审计日志", to: "/audit" },
  { label: "后台管理", to: "/admin" },
  { label: "设置", to: "/settings" },
];

export function CommandPalette({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const items = useMemo(() => {
    const kw = q.trim().toLowerCase();
    const pages = PAGES.filter((p) => !kw || p.label.toLowerCase().includes(kw)).map(
      (p) => ({ ...p, kind: "page" as const }),
    );
    const syms = mockSymbols
      .filter((s) => !kw || s.symbol.toLowerCase().includes(kw))
      .map((s) => ({
        label: s.symbol,
        to: `/market?symbol=${s.symbol}`,
        kind: "symbol" as const,
      }));
    return [...pages, ...syms].slice(0, 10);
  }, [q]);

  useEffect(() => {
    if (open) {
      setQ("");
      setIdx(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  useEffect(() => setIdx(0), [q]);

  if (!open) return null;

  const go = (to: string) => {
    navigate(to);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex justify-center bg-bg-0/70 pt-[16vh] backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="h-fit w-[560px] overflow-hidden rounded-lg border border-line bg-bg-2 shadow-3">
        <div className="flex items-center gap-2.5 border-b border-line-soft px-4 py-3">
          <Search size={15} className="text-fg-3" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setIdx((i) => Math.min(i + 1, items.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setIdx((i) => Math.max(i - 1, 0));
              } else if (e.key === "Enter" && items[idx]) {
                go(items[idx].to);
              } else if (e.key === "Escape") {
                onClose();
              }
            }}
            placeholder="搜索页面、交易对…"
            className="flex-1 bg-transparent text-sm text-fg-1 outline-none placeholder:text-fg-4"
          />
          <span className="rounded-[4px] border border-line bg-bg-3 px-1.5 py-0.5 font-mono text-micro text-fg-4">
            ESC
          </span>
        </div>
        <div className="max-h-[320px] overflow-auto p-1.5">
          {items.length === 0 && (
            <div className="px-3 py-6 text-center text-sm text-fg-4">
              无匹配结果
            </div>
          )}
          {items.map((it, i) => (
            <button
              key={it.kind + it.label}
              onClick={() => go(it.to)}
              onMouseEnter={() => setIdx(i)}
              className={`flex w-full cursor-pointer items-center gap-2.5 rounded-sm px-3 py-2 text-left text-sm ${
                i === idx ? "bg-bg-3 text-fg-1" : "text-fg-2"
              }`}
            >
              {it.kind === "symbol" ? (
                <CandlestickChart size={14} className="text-cyan" />
              ) : (
                <CornerDownLeft size={14} className="text-fg-4" />
              )}
              <span className={it.kind === "symbol" ? "font-mono" : ""}>
                {it.label}
              </span>
              <span className="ml-auto text-micro uppercase tracking-[.06em] text-fg-4">
                {it.kind === "symbol" ? "交易对" : "页面"}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
