/** 数字格式化 —— 与设计稿 shell.jsx 的 wfmt/wfmtPct/wfmtSigned 对齐 */

export function fmt(n: number, d = 2): string {
  return n.toLocaleString("en-US", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

export function fmtPct(n: number, d = 2): string {
  return (n >= 0 ? "+" : "") + n.toFixed(d) + "%";
}

export function fmtSigned(n: number): string {
  return (n >= 0 ? "+" : "−") + "$" + fmt(Math.abs(n));
}

/** 价格类数字：>=1000 保留 2 位，小币种保留更多有效位 */
export function fmtPrice(n: number): string {
  if (n >= 1000) return fmt(n, 2);
  if (n >= 1) return fmt(n, 2);
  return n.toPrecision(4);
}

export function fmtQty(n: number): string {
  return n.toLocaleString("en-US", { maximumFractionDigits: 6 });
}
