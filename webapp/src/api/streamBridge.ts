/**
 * WS → Query 缓存桥 —— 实时事件唯一入口：收到推送直接 patch 对应 query 缓存，
 * 页面只订阅 useQuery，不再各自 subscribe（docs/webapp前端架构.md S2）。
 */
import { qk, queryClient } from "./queryClient";
import { stream } from "./stream";
import type {
  AccountOverview,
  AccountSnapshot,
  Decision,
  EventItem,
  MarketSymbol,
} from "./types";

let started = false;

export function startStreamBridge() {
  if (started) return;
  started = true;

  stream.subscribe("risk.state", (r) => {
    queryClient.setQueryData(qk.risk, r);
  });

  stream.subscribe("account.snapshot", (snap) => {
    queryClient.setQueryData<AccountOverview>(qk.account, (prev) =>
      prev ? { ...prev, equity: snap.equity } : prev,
    );
    queryClient.setQueryData<AccountSnapshot[]>(qk.equityHistory, (prev) =>
      prev ? [...prev, snap].slice(-120) : prev,
    );
  });

  stream.subscribe("event.append", (e) => {
    queryClient.setQueryData<EventItem[]>(qk.events, (prev) =>
      prev ? [e, ...prev].slice(0, 60) : [e],
    );
  });

  stream.subscribe("decision.complete", (d) => {
    queryClient.setQueryData<Decision[]>(qk.decisions, (prev) =>
      prev ? [d, ...prev].slice(0, 20) : [d],
    );
    // 决策可能伴随持仓/订单变化，标脏让下次进入页面时重取
    void queryClient.invalidateQueries({ queryKey: qk.positions });
    void queryClient.invalidateQueries({ queryKey: qk.orders });
  });

  stream.subscribe("market.ticker", (t) => {
    queryClient.setQueryData<MarketSymbol[]>(qk.marketSymbols, (prev) =>
      prev?.map((s) =>
        s.symbol === t.symbol
          ? { ...s, price: t.price, changePct24h: t.changePct24h }
          : s,
      ),
    );
  });
}
