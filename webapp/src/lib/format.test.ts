import { describe, expect, it } from "vitest";
import { fmt, fmtPct, fmtSigned } from "./format";

describe("format", () => {
  it("fmt 千分位 + 两位小数", () => {
    expect(fmt(128450.7301)).toBe("128,450.73");
  });

  it("fmtPct 正值带 + 号", () => {
    expect(fmtPct(1.824)).toBe("+1.82%");
    expect(fmtPct(-0.5)).toBe("-0.50%");
  });

  it("fmtSigned 负值用 − 号（设计稿纪律）", () => {
    expect(fmtSigned(1248.05)).toBe("+$1,248.05");
    expect(fmtSigned(-54.3)).toBe("−$54.30");
  });
});
