/** 全局 QueryClient —— 服务端状态唯一缓存；WS 事件经 streamBridge 直写此缓存。 */
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/** Query key 约定：全部集中在这里，streamBridge 与页面共用，避免字符串漂移 */
export const qk = {
  risk: ["risk"] as const,
  account: ["account"] as const,
  equityHistory: ["account", "history"] as const,
  positions: ["positions"] as const,
  orders: ["orders"] as const,
  trades: ["trades"] as const,
  decisions: ["decisions"] as const,
  events: ["events"] as const,
  marketSymbols: ["market", "symbols"] as const,
  klines: (symbol: string, tf: string) => ["market", "klines", symbol, tf] as const,
  ticker: (symbol: string) => ["market", "ticker", symbol] as const,
  orderBook: (symbol: string) => ["market", "depth", symbol] as const,
  recentTrades: (symbol: string) => ["market", "trades", symbol] as const,
  perfSummary: ["performance", "summary"] as const,
  perfMonthly: ["performance", "monthly"] as const,
  perfAttribution: (dim: string) => ["performance", "attribution", dim] as const,
  strategies: ["strategies"] as const,
  hardLimits: ["hardLimits"] as const,
  symbolConfigs: ["symbolConfigs"] as const,
  labCandidates: ["lab", "candidates"] as const,
  labHistory: ["lab", "history"] as const,
  auditLogs: ["auditLogs"] as const,
  reports: ["reports"] as const,
  users: ["admin", "users"] as const,
  permissions: ["admin", "roles"] as const,
};
