# 2026-03-17 Runtime Config Frontend

## Chunk 2 — 前端配置面板

### 做了什么

1. 在 Dashboard 中新增“运行时配置中心”卡片
2. 支持在前端：
   - 切换 `testnet` / `mainnet`
   - 配置 Testnet API Key / Secret
   - 配置 Mainnet API Key / Secret
3. 不回显数据库中的 secret 明文，只展示“是否已配置”状态
4. 保存后调用后端配置 API，并提示“已热更新到当前进程”
5. 保留现有风险环境提示，让 mainnet 场景继续醒目警示

### 为什么这样做

用户希望后续可以在前端直接完成交易模式切换与密钥维护，而不是继续依赖手工改 `.env`。这一块前端面板是完整闭环里“可操作”的一半。

### 如何验证

- `cd frontend && npm run build`
- `cd backend && .venv/bin/pytest -q`

结果：前端 build 通过，backend 回归维持 **60 passed**。

### 当前状态

- 后端配置底座：已完成
- 前端基础配置面板：已完成
- 下一步：继续把更多可迁移配置从 env 下沉到数据库，并补配置 API 的更细测试
