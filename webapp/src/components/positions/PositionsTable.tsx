/** 持仓表 —— 对齐设计稿 pages.jsx WPositionsTable；detail 模式含 SL/TP/策略/操作列 */
import type { Position } from "@/api/types";
import { fmt, fmtPct, fmtQty, fmtSigned } from "@/lib/format";
import { Pill } from "@/components/ui/atoms";

const COIN_STYLE: Record<string, { bg: string; glyph: string }> = {
  BTC: { bg: "linear-gradient(135deg,#F7931A,#8B4E0D)", glyph: "₿" },
  ETH: { bg: "linear-gradient(135deg,#627EEA,#3C54BD)", glyph: "Ξ" },
};

export function CoinAvatar({ symbol, size = 22 }: { symbol: string; size?: number }) {
  const key = Object.keys(COIN_STYLE).find((k) => symbol.startsWith(k));
  const cfg = key
    ? COIN_STYLE[key]
    : { bg: "linear-gradient(135deg,var(--ap-bg-4),var(--ap-bg-3))", glyph: symbol[0] };
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full font-bold text-fg-1"
      style={{ width: size, height: size, background: cfg.bg, fontSize: size * 0.45 }}
    >
      {cfg.glyph}
    </div>
  );
}

const TH = ({ children }: { children: string }) => (
  <th className="px-3 py-2.5 text-left text-micro font-medium uppercase tracking-[.06em] text-fg-3">
    {children}
  </th>
);

const TD_MONO = "px-3 py-3 font-mono";

export function PositionsTable({
  positions,
  detail = false,
  onRowClick,
  onEdit,
  onClose,
}: {
  positions: Position[];
  detail?: boolean;
  onRowClick?: (p: Position) => void;
  onEdit?: (p: Position) => void;
  onClose?: (p: Position) => void;
}) {
  const heads = detail
    ? ["交易对", "方向", "数量", "入场", "标记", "浮盈", "收益率", "止损", "止盈", "持仓时长", "策略", "操作"]
    : ["交易对", "方向", "数量", "入场", "标记", "浮盈", "收益率", "持仓时长"];
  return (
    <div className="-mx-[18px] -my-4 overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-line">
            {heads.map((h) => (
              <TH key={h}>{h}</TH>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => {
            const isUp = p.pnl >= 0;
            const pnlCls = isUp ? "text-mint" : "text-rose";
            return (
              <tr
                key={p.id}
                className={`border-b border-line-soft ${onRowClick ? "cursor-pointer hover:bg-bg-3" : ""}`}
                onClick={() => onRowClick?.(p)}
              >
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <CoinAvatar symbol={p.symbol} />
                    <span className="font-mono font-semibold text-fg-1">
                      {p.symbol}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <Pill tone={p.side === "LONG" ? "mint" : "rose"}>{p.side}</Pill>
                </td>
                <td className={`${TD_MONO} text-fg-1`}>{fmtQty(p.qty)}</td>
                <td className={`${TD_MONO} text-fg-1`}>{fmt(p.entry)}</td>
                <td className={`${TD_MONO} text-fg-1`}>{fmt(p.mark)}</td>
                <td className={`${TD_MONO} ${pnlCls}`}>{fmtSigned(p.pnl)}</td>
                <td className={`${TD_MONO} ${pnlCls}`}>{fmtPct(p.pnlPct)}</td>
                {detail && <td className={`${TD_MONO} text-rose`}>{fmt(p.sl)}</td>}
                {detail && <td className={`${TD_MONO} text-mint`}>{fmt(p.tp)}</td>}
                <td className={`${TD_MONO} text-fg-3`}>{p.age}</td>
                {detail && <td className="px-3 py-3 text-fg-2">{p.strategy}</td>}
                {detail && (
                  <td className="whitespace-nowrap px-3 py-3">
                    {onEdit && onClose ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onEdit(p);
                          }}
                          className="mr-1 cursor-pointer rounded-xs border border-line bg-bg-3 px-2.5 py-1 text-xs text-fg-2 hover:text-fg-1"
                        >
                          编辑
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onClose(p);
                          }}
                          className="cursor-pointer rounded-xs border border-rose bg-rose-soft px-2.5 py-1 text-xs text-rose hover:brightness-110"
                        >
                          平仓
                        </button>
                      </>
                    ) : (
                      <span className="font-mono text-micro text-fg-4">只读</span>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
