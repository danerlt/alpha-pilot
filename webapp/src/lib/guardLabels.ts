/**
 * 守卫预检展示层：把后端下发的机器可读 check/note 翻译成人话。
 * 纯展示，不参与任何风控判定（verdict 仍以后端为准）。
 *
 * 语义分三态：
 *  - pass：通过（绿）
 *  - fail：真正被硬风控拦截（红）
 *  - skip：因输入不完整（未填止损/止盈/入场）暂时无法校验（琥珀·中性），
 *          不是违规，填齐后即可校验——避免把「还没填」误报成「违规」。
 */
import type { PrecheckItem } from "@/api/types";

export type GuardTone = "pass" | "fail" | "skip";

export interface GuardDisplay {
  /** 左侧中文标签 */
  label: string;
  /** 右侧一句话中文说明 */
  text: string;
  tone: GuardTone;
  /** 原始机器串，用于 title tooltip 供工程排查 */
  raw: string;
}

/** check key → { 中文标签, 通过话术, 拦截话术 } */
const GUARD_META: Record<string, { label: string; pass: string; fail: string }> = {
  kill_switch: { label: "系统急停", pass: "系统运行中", fail: "系统已急停，暂停下单" },
  daily_loss: { label: "当日亏损", pass: "当日亏损未超限", fail: "当日亏损已达熔断线" },
  consecutive_losses: { label: "连续亏损", pass: "连亏未超限", fail: "连续亏损已达上限" },
  balance: { label: "可用余额", pass: "余额充足", fail: "可用余额不足" },
  duplicate_position: { label: "重复持仓", pass: "无同向持仓", fail: "已持有该仓位" },
  position_size: { label: "单仓上限", pass: "未超单仓上限", fail: "超出单仓上限(20%)" },
  single_risk: { label: "单笔风险", pass: "单笔风险合规", fail: "单笔风险超限(1%)" },
  sl_distance: { label: "止损距离", pass: "止损距离合理", fail: "止损离入场太近或太远" },
  rr_ratio: { label: "盈亏比", pass: "盈亏比达标", fail: "盈亏比过低(需≥1.5)" },
  chaotic_regime: { label: "市场状态", pass: "市场状态正常", fail: "混沌行情，禁止开仓" },
  review: { label: "复核结论", pass: "未被否决", fail: "复核否决" },
  strategy_enabled: { label: "策略开关", pass: "手动单模式", fail: "策略未启用" },
  // 旧版/简化端点里出现过的 key，一并覆盖
  qty_valid: { label: "下单数量", pass: "数量合法", fail: "数量必须大于 0" },
  stop_loss_set: { label: "止损设置", pass: "止损已设置", fail: "开仓必须设置止损" },
  max_position_size: { label: "单仓上限", pass: "未超单仓上限", fail: "超出单仓上限(20%)" },
  daily_loss_limit: { label: "当日亏损", pass: "当日亏损未超限", fail: "当日亏损已达熔断线" },
  halted_check: { label: "系统急停", pass: "风控状态 OK", fail: "系统已急停" },
};

/** 只是「输入没填齐、暂时算不了」而非违规的 note 特征 → 归为 skip，并给出待填写提示 */
const SKIP_HINTS: Array<{ test: RegExp; text: string }> = [
  { test: /missing_sl_or_entry|no sl.*entry|missing.*entry/i, text: "缺止损或入场价，填写后校验" },
  { test: /no sl\/atr|no sl\b|missing.*sl/i, text: "填止损后校验" },
  { test: /no tp\/sl|no tp\b|missing.*tp/i, text: "填止盈/止损后校验" },
  { test: /skip/i, text: "输入不完整，暂无法校验" },
];

/** 把一条后端预检项转成人话展示 */
export function guardDisplay(item: PrecheckItem): GuardDisplay {
  const meta = GUARD_META[item.check];
  const label = meta?.label ?? item.check;
  const raw = item.note || item.check;

  if (item.pass) {
    return { label, text: meta?.pass ?? "通过", tone: "pass", raw };
  }

  // 未通过：先判是不是「只是没填齐」的 skip 态
  const skip = SKIP_HINTS.find((h) => h.test.test(item.note));
  if (skip) {
    return { label, text: skip.text, tone: "skip", raw };
  }

  return { label, text: meta?.fail ?? "未通过", tone: "fail", raw };
}
