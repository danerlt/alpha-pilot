/** API 层集成测试（MSW node）—— 重点覆盖守卫预检拒绝路径与响应包解包语义 */
import { describe, expect, it } from "vitest";
import { HttpResponse, http } from "msw";
import { server } from "@/test/setup";
import { ApiError } from "./client";
import { authApi, ordersApi, positionsApi } from "./services";

describe("守卫预检（拒绝路径必测）", () => {
  it("开仓未设止损 → REJECT，stop_loss_set 项 fail", async () => {
    const res = await ordersApi.precheck({
      symbol: "BTCUSDT",
      side: "BUY",
      type: "MARKET",
      qty: 0.01,
      reduceOnly: false,
    });
    expect(res.verdict).toBe("REJECT");
    const slItem = res.items.find((i) => i.check === "stop_loss_set");
    expect(slItem?.pass).toBe(false);
  });

  it("数量为 0 → REJECT", async () => {
    const res = await ordersApi.precheck({
      symbol: "BTCUSDT",
      side: "BUY",
      type: "MARKET",
      qty: 0,
      sl: 64000,
      reduceOnly: false,
    });
    expect(res.verdict).toBe("REJECT");
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
