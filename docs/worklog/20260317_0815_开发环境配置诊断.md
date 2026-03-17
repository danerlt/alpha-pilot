# 2026-03-17 Dev Config Diagnostics

## 问题

dev 环境后台日志持续出现：
- `API-key format invalid`（Binance）
- `invalid x-api-key`（LLM）
- `Empty LLM output`

在不读取真实 env 文件的规则下，本轮重点不是替换密钥，而是把**配置来源、诊断结果、降级行为**做清楚。

## 结论

### 当前运行路径
- 配置来源是 `get_settings()`
- `get_settings()` = `env 基础配置 + runtime DB overrides`
- Binance/LLM 客户端都通过运行时配置取 key

### 当前现象含义
- Binance key 当前对运行环境而言无效
- LLM key 当前对运行环境而言无效
- `Empty LLM output` 是上游 LLM 401 之后的连带现象，不是独立根因

## 本轮修复

1. 新增 `src/shared/config_diagnostics.py`
2. 在 `/health` 中返回：
   - `runtime_credentials.binance`
   - `runtime_credentials.llm`
3. 在 `/api/config/runtime` 中返回运行时凭据状态
4. 当检测到占位值或缺失值时：
   - Binance 客户端不再继续初始化外部调用
   - LLM 调用直接跳过并记录明确原因

## 结果

系统现在能明确告诉操作者：
- 当前密钥是否可用
- 是不是占位值 / 缺失值
- 问题是 Binance 侧还是 LLM 侧

## 推荐验证步骤

1. 访问 `/ap-dev/api/health`
2. 查看 `runtime_credentials`
3. 访问 `/ap-dev/api/config/runtime`
4. 在管理员配置中心检查：
   - 当前模式
   - Binance 凭据是否已配置
   - LLM key 是否已配置
5. 如果需要替换：
   - 通过管理员配置接口写入新值
   - 再看 `/health` 和后台日志

## 相关文件
- `backend/src/shared/config_diagnostics.py`
- `backend/src/services/decision_engine/engine.py`
- `backend/src/services/market_data/binance_client.py`
- `backend/src/app/router.py`
- `backend/tests/unit/test_config_diagnostics.py`
- `backend/tests/api/test_health.py`
