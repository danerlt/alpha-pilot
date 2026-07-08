/** API 层集成测试（MSW node）—— 重点覆盖守卫预检拒绝路径与响应包解包语义 */
import { describe, expect, it } from "vitest";
import { HttpResponse, http } from "msw";
import { server } from "@/test/setup";
import { ApiError } from "./client";
import { authApi, ordersApi, positionsApi } from "./services";

describe("守卫预检（拒绝路径必测）", () => {
  it("开仓未设止损 → REJECT，sl_distance 项 fail（soft）", async () => {
    const res = await ordersApi.precheck({
      symbol: "BTCUSDT",
      side: "BUY",
      type: "MARKET",
      qty: 0.01,
      reduceOnly: false,
    });
    expect(res.verdict).toBe("REJECT");
    const slItem = res.items.find((i) => i.check === "sl_distance");
    expect(slItem?.pass).toBe(false);
    expect(slItem?.category).toBe("soft");
  });

  it("名义超余额 → REJECT，balance 项 fail（physical 不可覆盖）", async () => {
    const res = await ordersApi.precheck({
      symbol: "BTCUSDT",
      side: "BUY",
      type: "MARKET",
      qty: 1,
      price: 68863,
      sl: 64000,
      tp: 80000,
      reduceOnly: false,
    });
    expect(res.verdict).toBe("REJECT");
    const balItem = res.items.find((i) => i.check === "balance");
    expect(balItem?.pass).toBe(false);
    expect(balItem?.category).toBe("physical");
  });

  it("设止损 + 合法数量 → PASS", async () => {
    const res = await ordersApi.precheck({
      symbol: "BTCUSDT",
      side: "BUY",
      type: "MARKET",
      qty: 0.01,
      sl: 64000,
      reduceOnly: false,
    });
    expect(res.verdict).toBe("PASS");
  });
});

describe("统一响应包解包", () => {
  it("success:false 抛 ApiError（业务异常 HTTP 200 语义）", async () => {
    server.use(
      http.get("/api/positions", () =>
        HttpResponse.json({
          success: false,
          code: "CIRCUIT_BREAKER",
          message: "已熔断",
          data: null,
        }),
      ),
    );
    await expect(positionsApi.list()).rejects.toThrowError(ApiError);
    await expect(positionsApi.list()).rejects.toThrowError("已熔断");
  });

  it("success:true 返回解包后的 data", async () => {
    const positions = await positionsApi.list();
    expect(Array.isArray(positions)).toBe(true);
    expect(positions[0]).toHaveProperty("symbol");
  });
});

describe("认证会话语义", () => {
  it("未登录 me 返回 401 → 抛 ApiError(401)", async () => {
    sessionStorage.removeItem("ap.mock.authed");
    await expect(authApi.me()).rejects.toMatchObject({ status: 401 });
  });

  it("login 建立会话后 me 正常返回", async () => {
    await authApi.login("a@b.c", "pw");
    const me = await authApi.me();
    expect(me.role).toBe("owner");
  });
});
