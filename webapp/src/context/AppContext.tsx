/**
 * 全局应用状态：风控状态（顶栏胶囊/HALTED 联动）、账户概览（侧栏权益）。
 * 初始值走 REST，此后由实时流（stream.ts）驱动：risk.state / account.snapshot。
 * setScene 为 mock 场景模拟入口（OK/WARN/HALTED 五件套联动演示，真后端下无效）。
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { AccountOverview, RiskState } from "@/api/types";
import { accountApi, riskApi } from "@/api/services";
import { stream, type Scene } from "@/api/stream";

interface AppState {
  risk: RiskState | null;
  account: AccountOverview | null;
  setScene: (s: Scene) => void;
  refresh: () => void;
}

const Ctx = createContext<AppState>({
  risk: null,
  account: null,
  setScene: () => {},
  refresh: () => {},
});

export function AppProvider({ children }: { children: ReactNode }) {
  const [risk, setRisk] = useState<RiskState | null>(null);
  const [account, setAccount] = useState<AccountOverview | null>(null);

  const refresh = useCallback(() => {
    riskApi.state().then(setRisk).catch(() => {});
    accountApi.overview().then(setAccount).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // 实时驱动：风控状态 + 账户权益
  useEffect(() => {
    const offRisk = stream.subscribe("risk.state", setRisk);
    const offAcct = stream.subscribe("account.snapshot", (snap) => {
      setAccount((prev) => (prev ? { ...prev, equity: snap.equity } : prev));
    });
    return () => {
      offRisk();
      offAcct();
    };
  }, []);

  const setScene = useCallback((s: Scene) => {
    stream.setScene(s);
  }, []);

  return (
    <Ctx.Provider value={{ risk, account, setScene, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useApp() {
  return useContext(Ctx);
}
