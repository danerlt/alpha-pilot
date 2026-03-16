# 2026-03-17 Runtime Config Implementation

## Chunk 1 — 后端配置底座

### 做了什么

1. 新增 `system_settings` 数据表与 Alembic migration：用于持久化运行时配置
2. 新增 `src/shared/runtime_config.py`：
   - 加密/解密敏感配置
   - 数据库配置加载为运行时 overrides
   - 选择当前 `trading_mode` 对应的 Binance 凭据
   - 配置更新后清理 Binance client 缓存
3. 改造 `src/shared/config.py`：
   - 基础设施配置仍从 `.env` 读取
   - 业务运行时配置支持数据库 override
   - 增加 `APP_CONFIG_MASTER_KEY` 用于敏感配置加密
4. 在 FastAPI 启动时预加载数据库配置并热刷新进内存
5. 新增后端配置 API：
   - `GET /api/config/runtime`
   - `POST /api/config/runtime`
6. 将新需求正式写入 README / PRD / worklog 排期

### 当前支持的数据库配置项

- 当前运行模式：`testnet` / `mainnet`
- Binance testnet API key / secret（加密存储）
- Binance mainnet API key / secret（加密存储）
- LLM provider / model / api key（api key 加密存储）
- 风控参数：
  - `max_position_size_pct`
  - `max_daily_loss_pct`
  - `max_consecutive_losses`
  - `max_single_risk_pct`

### 为什么这样做

这满足了“配置从 env 下沉到数据库，并支持前端维护”的基础前提，同时不直接改交易执行语义。

第一轮先把“配置来源”从纯 env 提升到 “env 基础设施配置 + db 运行时覆盖”，这样后续前端只需要调用配置 API，不必继续改动核心交易链路。

### 如何验证

- `cd backend && .venv/bin/pytest -q tests/unit/test_runtime_config.py tests/integration/test_migrations.py`
- `cd backend && .venv/bin/pytest -q`

结果：**60 passed**

### 下一步

Chunk 2 将继续做前端配置面板：

- 输入测试盘 / 实盘 API Key
- 切换 testnet / mainnet
- 不回显 secret 明文
- 更新后立即刷新界面状态
