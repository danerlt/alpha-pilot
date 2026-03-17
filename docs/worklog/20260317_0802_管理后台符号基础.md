# 2026-03-17 Admin Symbols Foundation

## 做了什么

完成管理员后台的数据层与第一批接口基础：

1. 新增 `symbol_configs` 表
2. 新增 `audit_logs` 表
3. 新增 Alembic migration：管理后台相关基础表
4. 新增管理员币种配置接口：
   - `GET /api/admin/symbols`
   - `POST /api/admin/symbols`
   - `PATCH /api/admin/symbols/{id}`
5. 创建/更新币种配置时写入审计日志
6. 补管理员币种配置专项测试

## 为什么做

这是管理后台正式落地前的关键后端基础：
- 币种管理需要独立配置表
- 后续管理员页面需要 CRUD API
- 审计日志是权限系统的重要配套，尤其适用于后台管理动作

## 如何验证

- `cd backend && .venv/bin/pytest -q tests/api/test_admin_symbols.py tests/unit/test_models.py tests/integration/test_migrations.py`
- `cd backend && .venv/bin/pytest -q`

结果：
- admin symbols/tests 通过
- backend **70 passed**

## 下一步

- 继续补管理员用户管理接口
- 补前端管理后台入口与页面
- 将 runtime config 页与 admin 身份体系联动
