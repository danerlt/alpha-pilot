# 20260705 handoff 后端 P2b + P3 — 行情 WS 代理 + Pilot AI 对话

## P2b · market.{symbol} WS 行情代理（handoff 3.1 收尾）

- **`/ws/market?token=<jwt>&symbol=BTCUSDT`**（`src/controllers/websocket_market.py`）：
  鉴权复用 /ws（4401/4403）；symbol 必须在 symbol_config 且 enabled 否则 4404（防任意字符串透传上游）；一连接一 symbol，换 symbol 重连。
- **MarketStreamManager**（`src/services/execution/market_stream.py`）：每 symbol 一个 hub 连
  Binance combined stream（ticker/depth10@100ms/trade，testnet/mainnet 域名随 TRADING_MODE），
  断线指数退避重连；**节流 250ms**（每类保留最新，trade 累积批次 ≤20 条）；订阅者有界队列，
  慢客户端满了丢消息不阻塞；无订阅者拆上游连接。盘口/逐笔**不落库**纯转发。
- 下行消息 `{"type": "market.ticker|market.depth|market.trades", "symbol", "ts", "data"}`，
  ticker 字段名与 REST Ticker24h 一致。
- 测试：归一化纯函数 4 例 + 管理器异步 4 例（pytest-asyncio）+ 端点 4 例（假上游注入，TestClient WS）。

## P3 · Pilot AI 对话（handoff 3.4）

- **`POST /api/agent/chat`**（SSE：`tool_call → delta → done`，登录可见）：
  prompt-based JSON 工具协议（兼容 DeepSeek/OpenAI/Mock，上限 4 轮，解析失败整段视为 final 兜底）；
  V1 伪流式（final 文本 64 字符切块发 delta，SSE 契约与真流式一致）；每次对话落 `agent_invocations`。
- **工具白名单（只读为主）**：get_positions / get_risk_state / get_decisions / get_decision /
  get_market_ticker / get_experiences；唯一写口 `propose_config_change` **只落 pending 行**。
- **pending action**：新表 `agent_pending_actions`（迁移 `20260705_204428_dab932bf4b22`）；
  可确认白名单 = runtime_config 四个 risk.* 键，**propose 与 confirm 双重校验**
  （守卫测试：数据层塞非法 key，confirm 也拒绝）。
- **`POST /api/agent/actions/{id}/confirm`**（admin）：白名单复核 → `upsert_system_setting`
  （Fernet 机制复用）→ runtime 刷新 → AuditLog。**`GET /api/agent/history`**（登录，typed）。
- LLM 装配 `dependencies.get_llm_client()`（占位 key 回退 Mock）。

## 验证

- 全量回归 **641 passed + 2 skipped**（P2b 前基线 615，净增 26 用例），ruff 全绿
- roadmap P3 验收覆盖：四类预设问题的工具链路（查持仓/解释决策/风险敞口/收紧风控→pending）
  单测走通；"Agent 无法绕过 confirm 直改配置"有三层测试（非白名单 propose 拒 /
  propose 只落 pending 不写配置 / confirm 复核白名单）
- openapi.json 重导（46 paths），前端可 `npm run gen:api`

## commits

- `0feaa15` feat(market): /ws/market Binance 行情 WS 代理（P2b）
- `60ab522` feat(agent): Pilot AI 对话域 — SSE 工具循环 + pending action 人工确认 + 历史（P3）

## 遗留

- agent chat 真流式（LLM client 支持 streaming 后把伪流式换掉，SSE 契约不变）
- 老板本机 dev 库欠 `make upgrade-db`（risk_events.decision_id + agent_pending_actions 两个迁移）
- 下一期 P4：settings 三组接口 + RBAC 四角色 + 2FA
