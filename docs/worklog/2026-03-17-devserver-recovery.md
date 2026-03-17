# 2026-03-17 Devserver Recovery

## 问题

dev server backend 容器反复重启，根因是：

- 数据库里已有历史 `create_all` 创建的核心表
- `alembic_version` 表存在但为空
- 启动时执行 `alembic upgrade head`，再次尝试跑初始 migration，触发 `DuplicateTable`

## 修复

### 提交
- `5b85b36` — `fix: recover legacy dev databases before alembic upgrade`

### 做了什么

1. 改造 `backend/scripts/upgrade_db.py`
2. 当检测到以下条件同时成立时：
   - 核心旧表已存在
   - `alembic_version` 存在但没有版本记录
3. 启动迁移前自动执行：
   - `alembic stamp 20260316_0001`
4. 然后再执行：
   - `alembic upgrade head`

这样可以让旧版 dev 数据库无损接入 Alembic 迁移链，而不用删库重建。

## 验证

- `cd backend && .venv/bin/pytest -q tests/unit/test_db_scripts.py tests/integration/test_migrations.py tests/api/test_health.py`
- `cd backend && .venv/bin/pytest -q`

结果：**61 passed**

## 后续

本次修复后已重新触发 `bash scripts/deploy-dev.sh`，待部署结果确认后应继续记录最终状态。
