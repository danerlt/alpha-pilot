# 2026-03-17 Auth Phase A

## 做了什么

完成用户中心 Phase A 基础能力：

1. 新增 `users` 数据模型与 Alembic migration
2. 新增角色与状态枚举：
   - `user` / `admin`
   - `active` / `disabled`
3. 新增认证服务：
   - password hash / verify
   - JWT create / decode
4. 新增认证 API：
   - `POST /api/auth/register`
   - `POST /api/auth/login`
   - `GET /api/auth/me`
5. 新增当前用户依赖与管理员依赖基础
6. 补 auth API 测试

## 当前范围

本阶段只做最小认证闭环，不包含：
- 用户管理后台页面
- 角色编辑页面
- 币种管理后台
- runtime config 权限化改造

这些将在后续阶段继续完成。

## 为什么这样做

先把身份边界和登录态做出来，后续管理后台和角色权限才能安全落地。

## 如何验证

- `cd backend && .venv/bin/pytest -q tests/api/test_auth.py`
- `cd backend && .venv/bin/pytest -q`

结果：
- auth API tests 通过
- backend **66 passed**
