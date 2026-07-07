/** 权限 hook —— 拒绝路径：viewer 不可手动下单；矩阵未加载时保守禁用 */
import { describe, expect, it } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { server } from "@/test/setup";
import { mockUsers } from "@/api/mock/data";
import { usePermission } from "./permissions";

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

function loginAs(role: "owner" | "viewer") {
  sessionStorage.setItem("ap.mock.authed", "1");
  server.use(
    http.get("/api/auth/me", () =>
      HttpResponse.json({
        success: true,
        code: "0",
        message: "ok",
        data: { ...mockUsers[0], role },
      }),
    ),
  );
}

describe("usePermission", () => {
  it("viewer 无 trade.manual（拒绝路径），有只读权限", async () => {
    loginAs("viewer");
    const { result } = renderHook(() => usePermission(), { wrapper });
    await waitFor(() => expect(result.current.role).toBe("viewer"));
    await waitFor(() => expect(result.current.can("trade.view")).toBe(true));
    expect(result.current.can("trade.manual_order")).toBe(false);
    expect(result.current.can("risk.edit_hard_limits")).toBe(false);
  });

  it("owner 拥有 trade.manual 与硬风控修改", async () => {
    loginAs("owner");
    const { result } = renderHook(() => usePermission(), { wrapper });
    await waitFor(() => expect(result.current.can("trade.manual_order")).toBe(true));
    expect(result.current.can("risk.edit_hard_limits")).toBe(true);
  });

  it("矩阵/用户未加载时保守返回 false", () => {
    sessionStorage.removeItem("ap.mock.authed");
    const { result } = renderHook(() => usePermission(), { wrapper });
    expect(result.current.can("trade.manual_order")).toBe(false);
  });
});
