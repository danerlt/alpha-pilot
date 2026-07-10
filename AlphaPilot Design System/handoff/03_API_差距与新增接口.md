# 03 · API 差距与新增接口

基线：仓库现有 API（positions/trades/decisions/risk-events/reports/account/auth/admin/commands/runtime-config/events/health + WS）。
下面按功能列**差距**与**新增契约**。落位遵循 `docs/project.md` 的 controller 分域（execution/risk/strategy/system）与统一响应/分页/异常规范；以下 body 仅描述业务字段。

## 3.1 行情（新域，建议 `controllers/api/v1/market/`）

| 接口 | 说明 |
|------|------|
| `GET /api/market/symbols` | 自选列表：价格/24h 涨跌/量、是否持仓、当前 regime |
| `GET /api/market/klines?symbol&interval&limit` | K线（market_data 服务已有拉取与存储，补查询端点） |
| `GET /api/market/ticker?symbol` | 24h 高低量、标记/指数价、资金费率、OI、下次结算时间 |
| WS 频道 `market.{symbol}` | ticker/盘口 top N/逐笔（Binance WS 代理转发，节流 ≥250ms） |

盘口与逐笔不落库，纯代理转发。

## 3.2 手动下单（execution 域扩展）

| 接口 | 说明 |
|------|------|
| `POST /api/orders/precheck` | **守卫预检**：body{symbol, side, type, qty, price?, sl?, tp?, reduce_only}；返回逐项检查 `[{check, pass, note}]` + 总判定。复用 execution_guard，同一套规则 |
| `POST /api/orders` | 手动下单。服务端**再次**过守卫（预检结果不可信任）；HALTED 时仅接受 reduce_only；写 Order+Trade，事件总线发布 |
| `PATCH /api/positions/{id}/sltp` | 修改止损止盈（走守卫；记审计） |

原则：人工单与 AI 单走同一 guard + 同一幂等 trace_id 机制（`manual:{user_id}:{client_order_id}`）。

## 3.3 决策流式可视化（WS 事件扩展）

策略管道各阶段发布进度事件（event_bus 已有，补事件类型）：

```
decision.progress {decision_id, stage: snapshot|reasoning|guard|verdict|execute,
                   status: start|done|fail, ts, payload?}
decision.complete {decision_id, action, confidence, guard, ...完整决策}
```

前端 StreamingDecision 订阅驱动逐段点亮；`GET /api/decisions/{id}` 返回完整详情（features 快照、守卫逐项、reasoning、关联订单）——decision 表已有，补 detail 端点。

## 3.4 Pilot AI 对话（新域 `agent/`，agent_invocation 表已有）

| 接口 | 说明 |
|------|------|
| `POST /api/agent/chat` | SSE 流式。事件：`tool_call {name, status}` → `delta {text}` → `done {invocation_id}` |
| `GET /api/agent/history?limit` | 会话历史 |
| `POST /api/agent/actions/{id}/confirm` | AI 提议的配置修改（如收紧风控）需人工确认后执行，落审计 |

Agent 工具白名单（只读为主）：查持仓/查决策/查风控状态/查经验库/查行情。**写操作一律生成 pending action 走 confirm**，Agent 无权直改硬风控。

## 3.5 策略实验室（新域 `lab/`，shadow 表已有）

| 接口 | 说明 |
|------|------|
| `GET /api/lab/candidates` | 候选列表：变更说明、来源、stage(queued/shadow/canary)、影子进度、影子 vs 线上指标对比 |
| `POST /api/lab/candidates` | 提交候选（人工提案；AI 提案由复盘服务生成） |
| `POST /api/lab/candidates/{id}/start` | 开始影子运行 |
| `POST /api/lab/candidates/{id}/promote` | 申请灰度/上线（服务端校验门槛：影子期≥60%、指标优于基线；需 admin 批准） |
| `POST /api/lab/candidates/{id}/terminate` | 终止归档 |
| `GET /api/lab/history` | promote/rollback/retire 时间线 |

影子执行：调度器对候选策略并行跑决策链但**不下单**，结果写 shadow 表逐笔对比。灰度回撤超限自动 rollback（monitoring 服务扩展）+ 事件通知。

## 3.6 设置（system 域扩展，system_setting 表已有）

| 接口 | 说明 |
|------|------|
| `GET/PUT /api/settings/exchange` | 交易所配置：网络(testnet/mainnet)、API Key（**写后只回脱敏尾 4 位**，加密存储） |
| `POST /api/settings/exchange/test` | 测试连接 + 返回权限清单 {read, trade, withdraw}；withdraw=true 返回警告 |
| `GET/PUT /api/settings/llm` | 提供方/模型/base_url/key(脱敏)/温度/超时 + per-agent 模型分工 |
| `POST /api/settings/llm/test` | 连通性测试 |
| `GET/PUT /api/settings/notifications` | 渠道绑定 + 事件订阅 |

密钥安全：DB 加密（Fernet，密钥来自环境变量）；任何 GET 永不回明文；修改记审计。**遵守仓库 env 黑白名单规则——真实密钥只经 API 写入 DB，不写 env 文件。**

## 3.7 RBAC 权限（system 域扩展，user/audit_log 表已有）

- user 表加 `role`：owner/admin/trader/viewer（唯一 owner）
- 权限矩阵硬编码为常量表（见设计稿 admin.jsx `PERMS`），FastAPI 依赖项 `require_permission("risk.edit_hard_limits")` 做端点守卫
- 关键动作 → 权限映射：修改硬风控/交易所/LLM 配置=admin+；手动下单/启停引擎/提交候选=trader+；批准上线/用户管理=admin+；其余只读=viewer+
- 新增：`GET /api/admin/roles`（矩阵展示）、`PATCH /api/admin/users/{id}`（改角色/状态，不能动 owner 与自己）、`POST /api/admin/users/{id}/approve`
- 2FA：TOTP（pyotp），登录二段式；`POST /api/auth/2fa/setup|verify`

## 3.8 绩效归因（strategy 域扩展，attribution 表已有）

| 接口 | 说明 |
|------|------|
| `GET /api/performance/summary?range` | 6 指标 + vs HODL 基准曲线 |
| `GET /api/performance/monthly` | 月度 PnL |
| `GET /api/performance/attribution?dim=symbol|strategy|trigger` | 归因分解 |

## 3.9 WS 事件类型汇总（前端订阅面）

```
risk.state        {state: OK|WARN|HALTED, day_loss_pct, positions_pct, regime}
decision.progress / decision.complete        （3.3）
position.update / order.update / account.snapshot
event.append      （事件流通用追加）
lab.update        （影子进度/自动回滚）
```

断线走已有 `/api/events/catchup` 补偿。
