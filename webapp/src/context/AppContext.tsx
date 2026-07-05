/**
 * 全局应用状态 hook —— 风控状态 + 账户概览，由 TanStack Query 缓存支撑；
 * 实时更新经 streamBridge 直写缓存，本模块不再自行订阅。
 * setScene 为 mock 场景模拟入口（HALTED 五件套演示，真后端下无效）。
 */
import { useCallback } from "react";
import { useAccount, useRiskState } from "@/api/queries";
import { stream, type Scene } from "@/api/stream";

export function useApp() {
  const { data: risk } = useRiskState();
  const { data: account } = useAccount();

  const setScene = useCallback((s: Scene) => {
    stream.setScene(s);
  }, []);

  return {
    risk: risk ?? null,
    account: account ?? null,
    setScene,
  };
}
