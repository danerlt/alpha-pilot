# 2026-03-17 Runtime Config API Tests

## 做了什么

为运行时配置中心补了 API 层回归测试：

- `GET /api/config/runtime`
  - 返回当前运行模式与风控/LLM配置概览
  - 仅返回“是否已配置”，不回显 secret
- `POST /api/config/runtime`
  - 验证会持久化更新项
  - 验证会触发 runtime refresh
  - 验证空 payload 返回 400

新增文件：
- `backend/tests/api/test_runtime_config.py`

## 为什么做

此前配置中心已有底座和前端面板，但 API 层缺少直接护栏。补上这层测试后，可以更稳定地保护：

- secret 不回显
- 更新行为不退化
- runtime refresh 不被删掉
- 空提交错误处理不回退

## 如何验证

- `cd backend && .venv/bin/pytest -q tests/api/test_runtime_config.py tests/api/test_health.py`
- `cd backend && .venv/bin/pytest -q`

结果：**64 passed**
