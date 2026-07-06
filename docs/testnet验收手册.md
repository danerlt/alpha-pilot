# AlphaPilot testnet 实盘验收手册（老板亲验清单）

> 覆盖 handoff 路线图 P1-P6 各期"testnet 实盘验收"项 + 24h 稳定性观察。
> 后端自动化测试已全绿（697 passed），本手册验证的是**真实链路**（真 Binance testnet、真 LLM、真前端）。

## 0. 前置（一次性）

```powershell
# 1. 依赖栈（PG 5442 + Redis 6389）
make deps-up          # 或 docker start alpha-pilot-postgres-1 alpha-pilot-redis-1

# 2. 迁移（已由 Claude 代跑到 head=99ca505e8d31，换机需重跑）
cd backend; $env:ALPHAPILOT_SKIP_SECRET_VALIDATION='1'; uv run python scripts/upgrade_db.py

# 3. .env 只需基础设施（新配置分层）：PG/Redis/APP_AUTH_SECRET_KEY/APP_CONFIG_MASTER_KEY/
#    DEFAULT_ADMIN_*；BINANCE_*/LLM_* 留空（走前端设置页）

# 4. 三个进程
cd backend; uv run python scripts/start_api.py        # api :8000
cd backend; uv run python scripts/start_scheduler.py  # scheduler（另开终端）
cd webapp;  npm run dev:real                          # 前端 :5174（同源代理，cookie 直通）
```

> 提速技巧：验收期可临时在 .env 设 `STRATEGY_LOOP_INTERVAL_MINUTES=2`，看完改回 15。

## 1. 配置链路（新配置分层验收）

- [ ] 登录（DEFAULT_ADMIN 账号）→ **设置→交易所连接**：填 Binance **testnet** Key →「测试连接」
      返回权限清单 `{read✓, trade✓, withdraw✗}`（**withdraw 若为 true 会出强警告，须换 Key**）→ 保存
- [ ] 刷新页面：Key 只显示 `****尾4位`，任何请求响应里无明文（F12 Network 抽查）
- [ ] **设置→AI 模型**：填 DeepSeek Key →「测试连接」返回 ok+延迟 → 保存
- [ ] （可选）**设置→通知**：填 Telegram bot token/chat_id；之后熔断类告警应推送到 TG
- [ ] 重启 api 与 scheduler：日志出现 `runtime settings loaded from DB (api_startup/scheduler_startup)`
      —— 证明 DB 配置在重启后仍生效（env 里没有 Key）

## 2. P1 · 决策流式（主控台）

- [ ] 等一轮策略循环：主控台 AI 决策卡**逐段点亮**（快照→推理→守卫→裁决→执行），完成后展开完整卡
- [ ] `GET /api/decisions` 列表出现新决策（带 guard_verdict / entry / sl / tp）；点击看详情（features/守卫/reasoning/关联订单）

## 3. P2 · 行情 + 手动下单

- [ ] 行情页：自选列表实时价格；K线加载；盘口/逐笔跳动（/ws/market）
- [ ] 手动下一单：OrderTicket 填参数 → 预检逐项 PASS → 下单 → 持仓页出现新仓位 → K线上出现 SL/TP 标线
- [ ] 风控页「暂停引擎」→ 顶栏胶囊变 HALTED → 再开一单（非 reduce-only）**必须被拒**（kill_switch 项 FAIL）→ reduce-only 平仓单放行 → 恢复引擎
- [ ] 改 SL/TP：给持仓改一个非法方向的 SL（高于现价）**必须被拒**

## 4. P3 · Pilot AI 对话（⌘J）

- [ ] 四个预设问题走通：查持仓 / 解释最近决策 / 风险敞口 / 「帮我把日亏熔断收紧到 2%」
- [ ] 最后一问应出现**待确认动作**（不直接生效）→ 管理员确认 → 风控页阈值变化 + 审计日志有记录
- [ ] 回答是流式逐字出现（真流式）

## 5. P4 · RBAC + 2FA

- [ ] 后台建一个 viewer 账号 → 用它登录 → 所有交易按钮不可用；直接 curl 下单接口返回 400004
- [ ] 建一个 pending 账号 → 该账号登录被拒 → 后台批准 → 可登录
- [ ] 自己开 2FA：设置→账户→扫码→验证 → 退出重登：出现 6 位验证码第二段 → 正确码进入
- [ ] （别忘了验收后视需要关闭 2FA，或妥善保存 TOTP）

## 6. P5 · 实验室（24h 项）

- [ ] 提交候选（推荐先 mirror 模式：`{"sl_mult": 0.8}`）→ 启动影子 → 24h 后回来看：
      影子进度条推进、影子 vs 线上对比表有数据
- [ ] 「申请灰度」在门槛未达时是禁用/报错的（进度 <60% 或样本 <3）
- [ ] （可选，注意 LLM 费用）提交 `{"mode": "llm"}` 候选：每周期每 symbol 一次独立 LLM 决策，
      决策流页面**不应**混入影子决策
- [ ] 回滚演练：候选 promote 到 CANARY 后，临时把日亏阈值调小（设置页 risk.max_daily_loss_pct）
      使当日亏损超过其 80% → 下一轮 lab job 自动 ROLLED_BACK + 历史时间线标 system + 事件流有 lab.update

## 7. P6 · 绩效

- [ ] 有若干笔已平仓交易后：绩效页指标磁贴/vs HODL 曲线/月度柱图/归因切换有数据
- [ ] 抽查对账：胜率 = 盈利笔数/总笔数 与交易记录页手数一致

## 8. 24h 稳定性观察点

- [ ] scheduler 日志：每 15 分钟 `strategy_pipeline summary`，无连续 ERROR
- [ ] 前端事件流持续滚动；断网 30 秒重连后事件不丢（catchup 补偿）
- [ ] `GET /api/health` 的 runtime_credentials 显示 binance/llm configured=true
- [ ] Redis/PG 容器内存无异常增长；event_outbox 表有 published_at 回填（shuttle 正常）

## 故障速查

| 现象 | 查什么 |
|------|--------|
| 决策卡不点亮 | scheduler 是否在跑；`runtime settings loaded` 是否出现；LLM Key 是否配置（占位 Key 恒 HOLD） |
| 下单失败 | 预检返回的具体 FAIL 项；testnet Key 权限；testnet 余额（水龙头充值） |
| WS 无数据 | /ws 与 /ws/market 连接状态（F12）；EventShuttle 日志 |
| 配置改了不生效 | api 立即生效当前 worker；scheduler 最迟一个策略周期；多 worker 部署重启 api |
