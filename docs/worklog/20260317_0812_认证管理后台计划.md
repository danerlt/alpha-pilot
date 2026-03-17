# 2026-03-17 Auth & Admin Plan

## 新需求

新增用户中心与管理后台：

- 用户注册 / 登录
- 角色：`user` / `admin`
- 管理后台
- 管理员可以维护币种相关配置
- 管理员不能看到 API Key / Secret 明文

## 排期拆分

### Phase A — 认证基础
- `users` 表
- password hash
- JWT 登录注册
- `/api/auth/register`
- `/api/auth/login`
- `/api/auth/me`

### Phase B — 权限基础
- `admin` 角色
- FastAPI 权限依赖
- 管理接口保护

### Phase C — 管理后台基础
- 用户列表 / 角色管理
- 币种配置表与 CRUD
- 审计日志表

### Phase D — 配置中心权限化
- runtime config API 改管理员权限
- 敏感配置只显示已配置/未配置
- 管理员只可写入，不可读明文

## 安全原则

- 密码只存哈希
- 敏感配置继续加密存储
- 管理员不可读 API Key / Secret 明文
- 关键管理动作进入审计日志
