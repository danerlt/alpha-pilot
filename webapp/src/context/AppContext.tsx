/**
 * 全局应用状态：风控状态（顶栏胶囊/HALTED 联动）、账户概览（侧栏权益）。
 * 真后端接入后由 WS risk.state / account.snapshot 事件驱动刷新。
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

interface AppState {
  risk: RiskState | null;
  account: AccountOverview | null;
  /** mock 演示用：模拟熔断联动（设计稿 HALTED 场景五件套） */
  setRiskOverride: (r: RiskState | null) => void;
  refresh: () => void;
}

const Ctx = createContext<AppState>({
  risk: null,
  account: null,
  setRiskOverride: () => {},
  refresh: () => {},
});

export function AppProvider({ children }: { children: ReactNode }) {
  const [risk, setRisk] = useState<RiskState | null>(null);
  const [account, setAccount] = useState<AccountOverview | null>(null);
  const [override, setOverride] = useState<RiskState | null>(null);

  const refresh = useCallback(() => {
    riskApi.state().then(setRisk).catch(() => {});
    accountApi.overview().then(setAccount).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <Ctx.Provider
      value={{
        risk: override ?? risk,
        account,
        setRiskOverride: setOverride,
        refresh,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useApp() {
  return useContext(Ctx);
}
