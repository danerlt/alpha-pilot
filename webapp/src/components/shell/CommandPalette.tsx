/** ⌘K 命令面板 —— 页面导航 + 交易对搜索 + 场景模拟（handoff/04 P0 验收项；场景模拟为 mock 演示） */
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CandlestickChart,
  Check,
  CornerDownLeft,
  Search,
  Siren,
} from "lucide-react";
import { mockSymbols } from "@/api/mock/data";
import { USE_MOCK } from "@/api/client";
import { useApp } from "@/context/AppContext";
import type { Scene } from "@/api/stream";

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

const SCENES: { label: string; scene: Scene; icon: typeof Check }[] = [
  { label: "场景 · 盈利运行（风控正常）", scene: "ok", icon: Check },
  { label: "场景 · 接近熔断阈值 WARN", scene: "warn", icon: AlertTriangle },
  { label: "场景 · 日亏熔断已触发 HALTED", scene: "halted", icon: Siren },
];

type Item =
  | { kind: "page"; label: string; to: string }
  | { kind: "symbol"; label: string; to: string }
  | { kind: "scene"; label: string; scene: Scene; icon: typeof Check };

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
  const { setScene } = useApp();

  const items = useMemo<Item[]>(() => {
    const kw = q.trim().toLowerCase();
    const pages: Item[] = PAGES.filter(
      (p) => !kw || p.label.toLowerCase().includes(kw),
    ).map((p) => ({ ...p, kind: "page" as const }));
    const syms: Item[] = mockSymbols
      .filter((s) => !kw || s.symbol.toLowerCase().includes(kw))
      .map((s) => ({
        kind: "symbol" as const,
        label: s.symbol,
        to: `/market?symbol=${s.symbol}`,
      }));
    const scenes: Item[] = USE_MOCK
      ? SCENES.filter(
          (s) => !kw || s.label.toLowerCase().includes(kw) || "场景".includes(kw),
        ).map((s) => ({ kind: "scene" as const, ...s }))
      : [];
    return [...pages, ...syms, ...scenes].slice(0, 14);
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

  const run = (it: Item) => {
    if (it.kind === "scene") {
      setScene(it.scene);
    } else {
      navigate(it.to);
    }
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
                run(items[idx]);
              } else if (e.key === "Escape") {
                onClose();
              }
            }}
            placeholder="搜索页面、交易对、场景…"
            className="flex-1 bg-transparent text-sm text-fg-1 outline-none placeholder:text-fg-4"
          />
          <span className="rounded-[4px] border border-line bg-bg-3 px-1.5 py-0.5 font-mono text-micro text-fg-4">
            ESC
          </span>
        </div>
        <div className="max-h-[360px] overflow-auto p-1.5">
          {items.length === 0 && (
            <div className="px-3 py-6 text-center text-sm text-fg-4">
              无匹配结果
            </div>
          )}
          {items.map((it, i) => (
            <button
              key={it.kind + it.label}
              onClick={() => run(it)}
              onMouseEnter={() => setIdx(i)}
              className={`flex w-full cursor-pointer items-center gap-2.5 rounded-sm px-3 py-2 text-left text-sm ${
                i === idx ? "bg-bg-3 text-fg-1" : "text-fg-2"
              }`}
            >
              {it.kind === "symbol" ? (
                <CandlestickChart size={14} className="text-cyan" />
              ) : it.kind === "scene" ? (
                <it.icon
                  size={14}
                  className={
                    it.scene === "halted"
                      ? "text-rose"
                      : it.scene === "warn"
                        ? "text-amber"
                        : "text-mint"
                  }
                />
              ) : (
                <CornerDownLeft size={14} className="text-fg-4" />
              )}
              <span className={it.kind === "symbol" ? "font-mono" : ""}>
                {it.label}
              </span>
              <span className="ml-auto text-micro uppercase tracking-[.06em] text-fg-4">
                {it.kind === "symbol" ? "交易对" : it.kind === "scene" ? "模拟" : "页面"}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
