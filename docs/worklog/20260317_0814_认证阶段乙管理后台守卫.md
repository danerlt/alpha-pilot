# 2026-03-17 Auth Phase B — Admin Guard

## 做了什么

完成用户权限 Phase B 的第一块：

1. 将 `POST /api/config/runtime` 切换为 **管理员权限接口**
2. 保留 `GET /api/config/runtime` 为只读概览接口
3. 新增管理员权限测试：
   - 普通用户/匿名用户不能更新 runtime config
   - 管理员可以更新 runtime config
4. 更新 runtime config 相关测试，使其显式通过 admin 身份验证

## 为什么做

运行时配置中心已经能写入：
- 交易模式
- Binance 凭据
- LLM 配置
- 风控参数

这些都属于管理级能力，不应该继续对匿名或普通用户开放。

## 如何验证

- `cd backend && .venv/bin/pytest -q tests/api/test_admin_permissions.py tests/api/test_runtime_config.py`
- `cd backend && .venv/bin/pytest -q`

结果：
- admin/runtime tests 通过
- backend **68 passed**

## 当前状态

- Auth Phase A：完成
- Auth Phase B（admin guard 第一块）：完成
- 下一步：继续补管理员用户管理、币种配置管理和后台页面入口
