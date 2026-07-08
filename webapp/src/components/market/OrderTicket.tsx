/**
 * 手动下单面板（handoff/02 P3）—— 守卫预检走后端 API（handoff/01：不在前端复算），
 * 未过预检禁用提交；HALTED 时仅允许 Reduce-Only。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Shield } from "lucide-react";
import type { OrderTicketPayload, PrecheckResult } from "@/api/types";
import { ordersApi } from "@/api/services";
import { useApp } from "@/context/AppContext";
import { usePermission } from "@/auth/permissions";
import { fmt } from "@/lib/format";
import { guardDisplay } from "@/lib/guardLabels";
import { Card, Dot, Pill } from "@/components/ui/atoms";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";

const INPUT_CLS =
  "w-full box-border rounded-sm border border-line bg-bg-3 px-2.5 py-2 font-mono text-xs text-fg-1 outline-none focus:border-line";
const LBL_CLS = "mb-1 block text-micro tracking-[.05em] text-fg-3";

type Side = "BUY" | "SELL";
type OType = "LIMIT" | "MARKET" | "STOP";

export function OrderTicket({ symbol, price }: { symbol: string; price: number }) {
  const { risk, account } = useApp();
  const { can } = usePermission();
  const canTrade = can("trade.manual_order");
  const [side, setSide] = useState<Side>("BUY");
  const [type, setType] = useState<OType>("LIMIT");
  const [priceStr, setPriceStr] = useState(String(Math.round(price)));
  const [qty, setQty] = useState("0.01");
  const [pct, setPct] = useState(25);
  const [sl, setSl] = useState("");
  const [tp, setTp] = useState("");
  const [reduceOnly, setReduceOnly] = useState(false);
  const [precheck, setPrecheck] = useState<PrecheckResult | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setPriceStr(String(Math.round(price)));
    setSubmitted(false);
  }, [symbol, price]);

  // 换交易对才关确认弹窗；价格实时跳动不应中断进行中的二次确认
  useEffect(() => {
    setConfirmOpen(false);
  }, [symbol]);

  const payload = useMemo<OrderTicketPayload>(
    () => ({
      symbol,
      side,
      type,
      qty: parseFloat(qty) || 0,
      price: type === "MARKET" ? undefined : parseFloat(priceStr) || undefined,
      sl: parseFloat(sl) || undefined,
      tp: parseFloat(tp) || undefined,
      reduceOnly,
    }),
    [symbol, side, type, qty, priceStr, sl, tp, reduceOnly],
  );

  // 守卫预检：输入变化 → debounce 调后端
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      ordersApi.precheck(payload).then(setPrecheck).catch(() => setPrecheck(null));
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [payload]);

  const effPrice = type === "MARKET" ? price : parseFloat(priceStr) || 0;
  const notional = (parseFloat(qty) || 0) * effPrice;
  const equity = account?.equity ?? 1;
  const posPct = (notional / equity) * 100;
  const rr = (() => {
    const s = parseFloat(sl);
    const t = parseFloat(tp);
    if (!effPrice || !s || !t) return null;
    const riskAmt = Math.abs(effPrice - s);
    return riskAmt > 0 ? Math.abs(t - effPrice) / riskAmt : null;
  })();

  const halted = risk?.state === "HALTED";
  const buySide = side === "BUY";
  const coin = symbol.replace("USDT", "");

  // ── 守卫失败项按服务端 category 分组 (判定权全在后端, 前端仅决定按钮形态与确认强度) ──
  const items = precheck?.items ?? [];
  const physicalFails = items.filter((i) => i.category === "physical" && !i.pass);
  const breakerFails = items.filter((i) => i.category === "breaker" && !i.pass);
  const softFails = items.filter((i) => i.category === "soft" && !i.pass);
  // 可覆盖项 = 软约束 + 熔断 (物理项永不可覆盖); 覆盖 key 列表提交给后端 override_checks
  const overridableFails = [...softFails, ...breakerFails];
  const overrideKeys = overridableFails.map((i) => i.check);
  const overrideCount = overridableFails.length;
  const hasBreakerOverride = breakerFails.length > 0;

  const qtyOk = payload.qty > 0;
  // 开仓缺止损铁律 (仅买入开仓; 平仓/reduce-only 不要求)
  const missingSl = buySide && !reduceOnly && !parseFloat(sl);

  // 三类死禁用 (灰禁, 不弹确认): 无权限 / 物理失败 / 开仓缺 SL。
  // HALTED 开新仓不再灰禁: precheck 的 kill_switch(category=breaker) 落入 breakerFails,
  // 走与其它熔断项一致的 amber + 强口令覆盖路径 (与后端 allowlist 对齐)。
  const hardBlocked =
    !canTrade || physicalFails.length > 0 || missingSl;

  // 直下 (绿/红, 无二次确认): 后端判 PASS, 或 HALTED 下 reduce-only 平仓
  const directPass =
    qtyOk && !hardBlocked && (precheck?.verdict === "PASS" || (halted && reduceOnly));
  // 可覆盖 (amber, 弹二次确认): 无死禁用触发, 非直下, 但有软/熔断可覆盖项
  const canOverride =
    qtyOk && !hardBlocked && !directPass && overrideCount > 0;
  const actionable = directPass || canOverride;

  // 提交: 直下→直接下单; 可覆盖→先弹确认, 由 ConfirmDialog 的 onConfirm 携带 overrideKeys 下单
  const submit = () => {
    if (busy || submitted) return;
    if (directPass) {
      void place([]);
    } else if (canOverride) {
      setConfirmOpen(true);
    }
  };

  const place = async (overrideChecks: string[]) => {
    if (busy) return;
    setBusy(true);
    try {
      await ordersApi.place({ ...payload, overrideChecks });
      setSubmitted(true);
      setConfirmOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="手动下单" right={<Pill tone="amber">人工干预</Pill>} className="h-fit">
      {/* 方向 */}
      <div className="mb-2.5 grid grid-cols-2 gap-1.5">
        {(
          [
            ["BUY", "买入 / 做多", "var(--ap-mint)"],
            ["SELL", "卖出 / 做空", "var(--ap-rose)"],
          ] as const
        ).map(([v, l, c]) => (
          <button
            key={v}
            onClick={() => setSide(v)}
            className="cursor-pointer rounded-sm border py-[9px] text-center text-xs font-bold"
            style={{
              background: side === v ? c : "var(--ap-bg-3)",
              color: side === v ? "var(--ap-bg-0)" : "var(--ap-fg-3)",
              borderColor: side === v ? c : "var(--ap-line)",
            }}
          >
            {l}
          </button>
        ))}
      </div>
      {/* 类型 */}
      <div className="mb-2.5 inline-flex rounded-sm border border-line bg-bg-3 p-0.5">
        {(
          [
            ["LIMIT", "限价"],
            ["MARKET", "市价"],
            ["STOP", "止损单"],
          ] as const
        ).map(([v, l]) => (
          <button
            key={v}
            onClick={() => setType(v)}
            className={`cursor-pointer rounded-xs px-3 py-[5px] font-mono text-xs ${type === v ? "bg-bg-4 text-fg-1" : "text-fg-3"}`}
          >
            {l}
          </button>
        ))}
      </div>

      {type !== "MARKET" && (
        <div className="mb-2.5">
          <span className={LBL_CLS}>价格 (USDT)</span>
          <input value={priceStr} onChange={(e) => setPriceStr(e.target.value)} className={INPUT_CLS} />
        </div>
      )}
      <div className="mb-2.5">
        <span className={LBL_CLS}>数量 ({coin})</span>
        <input value={qty} onChange={(e) => setQty(e.target.value)} className={INPUT_CLS} />
        <div className="mt-1.5 flex gap-1">
          {[10, 25, 50, 75, 100].map((p) => (
            <button
              key={p}
              onClick={() => {
                setPct(p);
                setQty((((equity * p) / 100 / price) * 0.1).toFixed(3));
              }}
              className={`flex-1 cursor-pointer rounded-[5px] border border-line-soft py-1 text-center font-mono text-micro ${
                pct === p ? "bg-bg-4 text-fg-1" : "bg-bg-3 text-fg-4"
              }`}
            >
              {p}%
            </button>
          ))}
        </div>
      </div>

      <div className="mb-2.5 grid grid-cols-2 gap-2">
        <div>
          <span className={LBL_CLS}>止损 SL</span>
          <input
            value={sl}
            onChange={(e) => setSl(e.target.value)}
            placeholder="必填"
            className={INPUT_CLS}
            style={{ borderColor: sl ? undefined : "rgba(255,77,109,.4)" }}
          />
        </div>
        <div>
          <span className={LBL_CLS}>止盈 TP</span>
          <input value={tp} onChange={(e) => setTp(e.target.value)} placeholder="可选" className={INPUT_CLS} />
        </div>
      </div>

      <button
        onClick={() => setReduceOnly(!reduceOnly)}
        className="mb-3 flex cursor-pointer items-center gap-2"
      >
        <span
          className="flex h-3.5 w-3.5 items-center justify-center rounded-[4px] border"
          style={{
            borderColor: reduceOnly ? "var(--ap-mint)" : "var(--ap-line)",
            background: reduceOnly ? "var(--ap-mint)" : "transparent",
          }}
        >
          {reduceOnly && <Check size={10} strokeWidth={3} style={{ color: "var(--ap-bg-0)" }} />}
        </span>
        <span className="text-xs text-fg-2">只减仓 Reduce-Only</span>
      </button>

      {/* 摘要 */}
      <div className="mb-2.5 flex flex-col gap-1 rounded-sm bg-bg-3 px-2.5 py-2 font-mono text-[10.5px]">
        <div className="flex justify-between">
          <span className="text-fg-4">名义价值</span>
          <span className="text-fg-1">${fmt(notional)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-fg-4">占用仓位</span>
          <span className={posPct > 15 ? "text-rose" : "text-fg-1"}>{posPct.toFixed(2)}%</span>
        </div>
        {rr !== null && (
          <div className="flex justify-between">
            <span className="text-fg-4">盈亏比</span>
            <span className={rr >= 1.5 ? "text-mint" : "text-rose"}>1:{rr.toFixed(2)}</span>
          </div>
        )}
      </div>

      {/* 守卫预检（后端返回逐项） */}
      <div className="mb-3">
        <div className="mb-1.5 flex items-center gap-1.5 text-micro font-semibold tracking-[.06em] text-fg-3">
          <Shield size={11} /> 守卫预检 · 人工单同样受硬风控约束
        </div>
        <div className="flex flex-col gap-[3px]">
          {(precheck?.items ?? []).map((c) => {
            const g = guardDisplay(c);
            const dotColor =
              g.tone === "pass"
                ? "var(--ap-mint)"
                : g.tone === "skip"
                  ? "var(--ap-amber)"
                  : "var(--ap-rose)";
            const textColor =
              g.tone === "pass"
                ? "var(--ap-fg-2)"
                : g.tone === "skip"
                  ? "var(--ap-amber)"
                  : "var(--ap-rose)";
            return (
              <div key={c.check} className="flex items-center gap-1.5 text-[10.5px]" title={g.raw}>
                <Dot color={dotColor} />
                <span className="flex-1 text-fg-3">{g.label}</span>
                <span className="text-right font-mono" style={{ color: textColor }}>
                  {g.text}
                </span>
              </div>
            );
          })}
          {!precheck && (
            <div className="font-mono text-[10.5px] text-fg-4">预检中…</div>
          )}
        </div>
      </div>

      <button
        onClick={submit}
        disabled={!actionable || busy || submitted}
        className="w-full cursor-pointer rounded-[9px] border-none py-[11px] text-sm font-bold disabled:cursor-not-allowed"
        style={{
          background: submitted
            ? "var(--ap-bg-4)"
            : canOverride
              ? "var(--ap-amber)"
              : directPass
                ? buySide
                  ? "var(--ap-mint)"
                  : "var(--ap-rose)"
                : "var(--ap-bg-4)",
          color: submitted
            ? "var(--ap-mint)"
            : actionable
              ? "var(--ap-bg-0)"
              : "var(--ap-fg-4)",
        }}
      >
        {submitted
          ? "已提交"
          : busy
            ? "提交中…"
            : !canTrade
              ? "无手动下单权限"
              : physicalFails.length > 0
                ? "余额不足 / 无持仓，无法下单"
                : missingSl
                  ? "请先填止损"
                  : canOverride
                    ? `强行下单（覆盖 ${overrideCount} 项）`
                    : directPass
                      ? `${buySide ? "买入" : "卖出"} ${coin}`
                      : "守卫未通过"}
      </button>

      {/* 覆盖守卫二次确认: 含熔断项走强口令 OVERRIDE, 纯软约束普通确认 */}
      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={() => void place(overrideKeys)}
        busy={busy}
        requireText={hasBreakerOverride ? "OVERRIDE" : undefined}
        confirmLabel="确认强行下单"
        title="强行下单 · 覆盖守卫拦截"
        body={
          <div className="flex flex-col gap-3">
            {hasBreakerOverride && (
              <div className="font-semibold text-rose">
                你正在覆盖 {overrideCount} 项熔断/风控，此操作将被记录审计。
              </div>
            )}
            <div className="text-fg-2">
              确认后将<span className="font-semibold text-rose">绕过以下守卫拦截</span>直接下单：
            </div>
            <ul className="flex flex-col gap-1.5">
              {overridableFails.map((it) => {
                const g = guardDisplay(it);
                return (
                  <li key={it.check} className="flex items-center justify-between gap-3">
                    <span className="text-fg-1">{g.label}</span>
                    <span className="font-mono text-xs text-rose">{g.text}</span>
                  </li>
                );
              })}
            </ul>
            <div className="text-xs text-rose">
              绕过硬风控属高危操作，请确认已知晓并自行承担风险。
            </div>
          </div>
        }
      />
    </Card>
  );
}
