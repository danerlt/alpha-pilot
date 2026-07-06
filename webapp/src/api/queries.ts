/** 页面数据 hooks —— 页面只用这里，不直接碰 services/fetch。 */
import { useQuery } from "@tanstack/react-query";
import { qk } from "./queryClient";
import {
  accountApi,
  adminApi,
  auditApi,
  decisionsApi,
  eventsApi,
  labApi,
  marketApi,
  ordersApi,
  performanceApi,
  positionsApi,
  riskApi,
  strategyApi,
  tradesApi,
} from "./services";
import type { AttributionDim } from "./types";

export const useRiskState = () =>
  useQuery({ queryKey: qk.risk, queryFn: riskApi.state });

export const useAccount = () =>
  useQuery({ queryKey: qk.account, queryFn: accountApi.overview });

export const useEquityHistory = () =>
  useQuery({ queryKey: qk.equityHistory, queryFn: accountApi.history });

export const usePositions = () =>
  useQuery({ queryKey: qk.positions, queryFn: positionsApi.list });

export const useOrders = () =>
  useQuery({ queryKey: qk.orders, queryFn: ordersApi.list });

export const useTrades = () =>
  useQuery({ queryKey: qk.trades, queryFn: tradesApi.list });

export const useDecisions = () =>
  useQuery({ queryKey: qk.decisions, queryFn: decisionsApi.list });

export const useEvents = () =>
  useQuery({ queryKey: qk.events, queryFn: eventsApi.recent });

export const useMarketSymbols = () =>
  useQuery({ queryKey: qk.marketSymbols, queryFn: marketApi.symbols });

export const useKlines = (symbol: string, tf: string, limit = 64) =>
  useQuery({
    queryKey: qk.klines(symbol, tf),
    queryFn: () => marketApi.klines(symbol, tf, limit),
  });

export const useTicker = (symbol: string) =>
  useQuery({
    queryKey: qk.ticker(symbol),
    queryFn: () => marketApi.ticker(symbol),
  });

export const usePerformanceSummary = () =>
  useQuery({ queryKey: qk.perfSummary, queryFn: performanceApi.summary });

export const usePerformanceMonthly = () =>
  useQuery({ queryKey: qk.perfMonthly, queryFn: performanceApi.monthly });

export const useAttribution = (dim: AttributionDim) =>
  useQuery({
    queryKey: qk.perfAttribution(dim),
    queryFn: () => performanceApi.attribution(dim),
  });

export const useStrategies = () =>
  useQuery({ queryKey: qk.strategies, queryFn: strategyApi.list });

export const useHardLimits = () =>
  useQuery({ queryKey: qk.hardLimits, queryFn: strategyApi.hardLimits });

export const useSymbolConfigs = () =>
  useQuery({ queryKey: qk.symbolConfigs, queryFn: strategyApi.symbolConfigs });

export const useLabCandidates = () =>
  useQuery({ queryKey: qk.labCandidates, queryFn: labApi.candidates });

export const useLabHistory = () =>
  useQuery({ queryKey: qk.labHistory, queryFn: labApi.history });

export const useAuditLogs = () =>
  useQuery({ queryKey: qk.auditLogs, queryFn: auditApi.logs });

export const useReports = () =>
  useQuery({ queryKey: qk.reports, queryFn: auditApi.reports });

export const useUsers = () =>
  useQuery({ queryKey: qk.users, queryFn: adminApi.users });

export const usePermissions = () =>
  useQuery({ queryKey: qk.permissions, queryFn: adminApi.permissions });
