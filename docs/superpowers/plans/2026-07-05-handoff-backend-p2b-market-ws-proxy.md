# Handoff 后端 P2b — market.{symbol} WS 行情代理 实现计划

> 依据：handoff/03 §3.1（WS 频道 market.{symbol}：ticker/盘口 top N/逐笔，Binance WS 代理转发，
> 节流 ≥250ms，盘口与逐笔**不落库**纯转发）+ webapp 架构 B2。
> 执行：本会话内联 TDD，每 task 提交推送。

## 设计

- **新 WS 端点 `/ws/market?token=<jwt>&symbol=BTCUSDT`**：一连接一 symbol（前端行情页一次看一个，
  换 symbol 重连）；鉴权复用 `/ws` 的 `_verify_token/_verify_user_active`（4401/4403）；
  symbol 必须在 symbol_config 且 enabled，否则 close 4404（防任意字符串透传上游）。
- **MarketStreamManager**（`src/services/execution/market_stream.py`，api 进程内单例）：
  - 每 symbol 一个 hub：上游任务连 Binance combined stream
    （`{sym}@ticker / {sym}@depth10@100ms / {sym}@trade`，testnet= `wss://testnet.binance.vision/stream`，
    mainnet=`wss://stream.binance.com:9443/stream`），断线指数退避重连；
    无订阅者时拆除上游连接。
  - **节流**：per (symbol, kind) 保留最新（trade 累积本窗口列表，上限 20 条），
    flusher 每 250ms 推给全部订阅者。
  - 订阅者 = `asyncio.Queue(maxsize=100)`；慢客户端队列满直接丢消息（不阻塞其他订阅者）。
  - `upstream_factory` 可注入（测试用假上游 async generator）。
- **下行消息格式**（不走 Response envelope，与 /ws 一致直推）：
  `{"type": "market.ticker"|"market.depth"|"market.trades", "symbol": "...", "ts": ..., "data": ...}`
  - ticker data 与 REST `Ticker24h` 字段名一致（last_price/price_change_pct/high_24h/...）
  - depth data: `{bids: [[price, qty]×10], asks: [...]}`
  - trades data: `[{price, qty, side: buy|sell, ts}]`

## Tasks

1. **归一化纯函数 + 节流 hub**（TDD，纯逻辑可同步测）：`_normalize_stream_message(symbol, raw)`；
   hub 的 store/flush 逻辑。
2. **MarketStreamManager 异步壳**（pytest-asyncio）：subscribe/unsubscribe/fan-out/无订阅者拆 hub/
   慢客户端丢消息。
3. **`/ws/market` 端点 + app.py 注册**：鉴权（无 token 4401）、symbol 校验（4404）、
   订阅→pump→断线清理；TestClient WS 测试（假上游注入）。
4. 收口：全量回归 + ruff + worklog + openapi 无需重导（WS 不进 OpenAPI）+ 更新记忆。
