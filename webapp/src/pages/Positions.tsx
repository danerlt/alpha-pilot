/**
 * 持仓与订单（handoff/02 P5）—— 4 磁贴 + 持仓表（编辑 SL/TP 走守卫预检、平仓二次确认）
 * + 订单簿表 + 空态。
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Layers } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Dot, Pill, Stat } from "@/components/ui/atoms";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { PositionsTable } from "@/components/positions/PositionsTable";
import { useOrders, usePositions } from "@/api/queries";
import { usePermission } from "@/auth/permissions";
import { qk } from "@/api/queryClient";
import { ordersApi, positionsApi } from "@/api/services";
import type { Position, PrecheckResult } from "@/api/types";
import { fmt, fmtSigned } from "@/lib/format";

export default function Positions() {
  const queryClient = useQueryClient();
  const { can } = usePermission();
  const canTrade = can("trade.manual_order");
  const { data: positions = [] } = usePositions();
  const { data: orders = [] } = useOrders();
  const [editing, setEditing] = useState<Position | null>(null);
  const [closing, setClosing] = useState<Position | null>(null);
  const [busy, setBusy] = useState(false);
  const [sl, setSl] = useState("");
  const [tp, setTp] = useState("");
  const [precheck, setPrecheck] = useState<PrecheckResult | null>(null);

  const reload = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: qk.positions });
    void queryClient.invalidateQueries({ queryKey: qk.orders });
  }, [queryClient]);

  // 编辑 SL/TP：打开时预填 + 守卫预检
  useEffect(() => {
    if (!editing) {
      setPrecheck(null);
      return;
    }
    setSl(String(editing.sl));
    setTp(String(editing.tp));
  }, [editing]);

  useEffect(() => {
    if (!editing) return;
    const t = setTimeout(() => {
      ordersApi
        .precheck({
          symbol: editing.symbol,
          side: "SELL",
          type: "STOP",
          qty: editing.qty,
          sl: parseFloat(sl) || undefined,
          tp: parseFloat(tp) || undefined,
          reduceOnly: true,
        })
        .then(setPrecheck)
        .catch(() => setPrecheck(null));
    }, 300);
    return () => clearTimeout(t);
  }, [editing, sl, tp]);

  const totalPnl = useMemo(
    () => positions.reduce((s, p) => s + p.pnl, 0),
    [positions],
  );
  const working = orders.filter((o) => o.status === "WORKING");

  const saveSltp = async () => {
    if (!editing) return;
    setBusy(true);
    try {
      await positionsApi.updateSltp(editing.id, parseFloat(sl), parseFloat(tp));
      setEditing(null);
      reload();
    } finally {
      setBusy(false);
    }
  };

  const doClose = async () => {
    if (!closing) return;
    setBusy(true);
    try {
      await positionsApi.close(closing.id);
      setClosing(null);
      reload();
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageShell title="持仓与订单" sub="POSITIONS">
      <div className="flex flex-col gap-5">
        {/* 磁贴 ×4 */}
        <div className="grid grid-cols-2 gap-3 min-[900px]:grid-cols-4">
          <Card dense>
            <Stat label="总持仓" value={positions.length} sub={`占比 ${positions.reduce((s, p) => s + p.marginPct, 0).toFixed(1)}%`} />
          </Card>
          <Card dense>
            <Stat
              label="多头"
              value={positions.filter((p) => p.side === "LONG").length}
              sub={positions.map((p) => p.symbol.replace("USDT", "")).join(" · ") || "—"}
            />
          </Card>
          <Card dense>
            <Stat
              label="浮盈总计"
              value={fmtSigned(totalPnl)}
              tone={totalPnl >= 0 ? "pos" : "neg"}
            />
          </Card>
          <Card dense>
            <Stat
              label="活跃挂单"
              value={working.length}
              sub={`SL×${working.filter((o) => o.type === "STOP").length} · TP×${working.filter((o) => o.type === "TAKE_PROFIT").length}`}
            />
          </Card>
        </div>

        {/* 持仓表 */}
        <Card title="持仓">
          {positions.length > 0 ? (
            <PositionsTable
              positions={positions}
              detail
              onEdit={canTrade ? (p) => setEditing(p) : undefined}
              onClose={canTrade ? (p) => setClosing(p) : undefined}
            />
          ) : (
            <div className="flex flex-col items-center justify-center gap-2.5 px-6 py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-md bg-bg-3">
                <Layers size={22} className="text-fg-4" />
              </div>
              <div className="text-sm font-semibold text-fg-2">暂无持仓</div>
              <div className="max-w-[280px] text-xs text-fg-4">
                AI 正在等待入场信号，符合策略条件时将自动开仓
              </div>
            </div>
          )}
        </Card>

        {/* 订单簿 */}
        <Card title="订单簿">
          <div className="-mx-[18px] -my-4 overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="border-b border-line">
                  {["时间", "交易对", "方向", "类型", "数量", "价格", "状态"].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2.5 text-left text-micro font-medium uppercase tracking-[.06em] text-fg-3"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id} className="border-b border-line-soft">
                    <td className="px-3 py-2.5 font-mono text-fg-3">{o.ts}</td>
                    <td className="px-3 py-2.5 font-mono font-semibold text-fg-1">{o.symbol}</td>
                    <td className="px-3 py-2.5">
                      <Pill tone={o.side === "BUY" ? "mint" : "rose"}>{o.side}</Pill>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-[11px] text-fg-2">{o.type}</td>
                    <td className="px-3 py-2.5 font-mono text-fg-1">{o.qty}</td>
                    <td className="px-3 py-2.5 font-mono text-fg-1">{fmt(o.price)}</td>
                    <td className="px-3 py-2.5">
                      <Pill tone={o.status === "FILLED" ? "mint" : o.status === "WORKING" ? "cyan" : "default"}>
                        {o.status}
                      </Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* 编辑 SL/TP */}
      <Modal
        open={editing !== null}
        onClose={() => setEditing(null)}
        title={editing ? `编辑止损止盈 · ${editing.symbol}` : ""}
      >
        {editing && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="mb-1 text-micro tracking-[.05em] text-fg-3">止损 SL</div>
                <input
                  value={sl}
                  onChange={(e) => setSl(e.target.value)}
                  className="w-full rounded-sm border border-line bg-bg-4 px-3 py-2 font-mono text-sm text-rose outline-none focus:border-rose"
                />
              </div>
              <div>
                <div className="mb-1 text-micro tracking-[.05em] text-fg-3">止盈 TP</div>
                <input
                  value={tp}
                  onChange={(e) => setTp(e.target.value)}
                  className="w-full rounded-sm border border-line bg-bg-4 px-3 py-2 font-mono text-sm text-mint outline-none focus:border-mint"
                />
              </div>
            </div>
            <div className="font-mono text-xs text-fg-4">
              入场 {fmt(editing.entry)} · 标记 {fmt(editing.mark)}
            </div>
            {/* 守卫预检 */}
            <div className="flex flex-col gap-1">
              {(precheck?.items ?? []).map((c) => (
                <div key={c.check} className="flex items-center gap-1.5 font-mono text-[10.5px]">
                  <Dot color={c.pass ? "var(--ap-mint)" : "var(--ap-rose)"} />
                  <span className="flex-1 text-fg-3">{c.check}</span>
                  <span className={c.pass ? "text-fg-2" : "text-rose"}>{c.note}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setEditing(null)}>
                取消
              </Button>
              <Button
                variant="primary"
                disabled={busy || precheck?.verdict !== "PASS"}
                onClick={saveSltp}
              >
                {busy ? "保存中…" : "保存修改"}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* 平仓确认 */}
      <ConfirmDialog
        open={closing !== null}
        onClose={() => setClosing(null)}
        onConfirm={doClose}
        busy={busy}
        title={closing ? `平仓确认 · ${closing.symbol}` : ""}
        confirmLabel="确认平仓"
        body={
          closing && (
            <>
              将以市价平掉 <b className="font-mono text-fg-1">{closing.qty} {closing.symbol.replace("USDT", "")}</b>
              ，当前浮盈{" "}
              <b className={`font-mono ${closing.pnl >= 0 ? "text-mint" : "text-rose"}`}>
                {fmtSigned(closing.pnl)}
              </b>
              。此操作绕过 AI 决策，直接提交交易所执行。
            </>
          )
        }
      />
    </PageShell>
  );
}
