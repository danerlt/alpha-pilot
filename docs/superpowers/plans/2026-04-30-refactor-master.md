# AlphaPilot 后端按 FastAPI 模板 v3 全量重构 — Master Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 AlphaPilot 后端按 `docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` (v3.6) 的设计全量重构，分 5 阶段渐进交付，每阶段独立可部署可回滚。

**Architecture:** B-Hybrid 目录布局（DB 层扁平 + 业务层按领域聚合）+ 同步 SQLAlchemy + APScheduler + Redis List 任务队列；api / scheduler 双容器部署；不引入 funboost。

**Tech Stack:** Python 3.12 + FastAPI 0.128+ + SQLAlchemy 2.x + PostgreSQL 16 + Redis 7 + APScheduler 3.x + uv 包管理 + Alembic 1.18+ + asgi-correlation-id + pytest

**关联文档：**
- 设计 spec：`docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` (v3.6)
- 模板原文：`docs/fastapi-project-template-v3.md`
- 项目记忆：`.claude/memory/MEMORY.md` / `CLAUDE.md`

---

## 五阶段 Plan 文件

| 阶段 | Plan 文件 | 状态 |
|------|----------|------|
| 阶段 1：基础设施层 | `docs/superpowers/plans/2026-04-30-refactor-stage1-infrastructure.md` | ✅ 已展开 |
| 阶段 2：DB 层扁平化 + 主键升级 | （阶段 1 完成后展开） | ⏳ 待展开 |
| 阶段 3：业务层重组 | （阶段 2 完成后展开） | ⏳ 待展开 |
| 阶段 4：响应/异常体系切换 | （阶段 3 完成后展开） | ⏳ 待展开 |
| 阶段 5：scheduler 进程拆分 | （阶段 4 完成后展开） | ⏳ 待展开 |

**为什么不一次写完所有 plan？**

每阶段的实施会让 spec 中的某些假设变得精确（如 service 接口、cruds 方法签名）。提前展开 2-5 阶段会基于"假设的"接口写 task，到了阶段 N 实施时会大量返工。**渐进展开 = 每阶段 plan 都基于已验收的现实**。

---

## 五阶段依赖图

```
阶段 1: 基础设施层
   ├─ src/db/{engines,session,migrate}.py
   ├─ src/configs/app_configs.py（8 个子配置）
   ├─ src/common/{response,exception,pagination,enums,constants,api_response}/
   ├─ src/utils/{log,redis,time,uuid,request_id,json,serializers}/
   ├─ src/middleware/{request_logging,error_logging}/
   ├─ src/app.py（提级；保留 src/app/routers/ 暂不动）
   └─ 验收：HTTP 行为零变化，request_id 注入日志
        │
        ▼
阶段 2: DB 层扁平化 + 主键升级
   ├─ src/models/（17 实体平铺，BigInt id + TradingModeMixin 按需）
   ├─ src/cruds/（base_crud + 17 实体 crud）
   ├─ src/schemas/（平铺，Pydantic）
   ├─ migrations/versions/ 全删 + alembic revision --autogenerate
   └─ 验收：干净库 alembic upgrade head 通过 + 测试全绿
        │
        ▼
阶段 3: 业务层重组
   ├─ src/services/{execution,insight,strategy,risk}/
   ├─ src/core/{exchange,llm,indicators,trace}/
   ├─ src/events/* → src/common/events.py + services/event_bus.py + cruds/{outbox,inbox}_crud.py
   └─ 验收：HTTP/WebSocket/scheduler 行为零变化
        │
        ▼
阶段 4: 响应/异常体系切换 ⚠️ Breaking Change
   ├─ src/controllers/api/v1/{domain}/（重组）
   ├─ Response[T] + @api_response + 异常树（AppBaseException 自动 ERROR）
   ├─ 前端 fetch 封装升级（解 data 字段、判 success+code、读 request_id）
   └─ 验收：后端测试全绿 + 前端 e2e 跑通
        │
        ▼
阶段 5: scheduler 进程拆分 + APScheduler 持久化
   ├─ scripts/start_api.py + scripts/start_scheduler.py
   ├─ src/schedulers/{strategy_pipeline_scanner,position_monitor_scanner,event_shuttle}.py
   ├─ docker-compose 改造：api service（多 worker）+ scheduler service（单容器，stop_grace_period: 60s）
   ├─ src/app.py lifespan 移除 scheduler 启动
   └─ 验收：scheduler 重启 job 不丢 + 多 worker WebSocket 跑通 + dev 24h 观察
```

---

## 跨阶段总验收清单（合并主分支前）

- [ ] 5 个阶段都已合并
- [ ] `tests/` 全绿（单测 + 集成测试），覆盖率 ≥ 当前水平
- [ ] 前端 e2e 通过
- [ ] dev server 上线运行 ≥ 24h，无异常
- [ ] `make dev-up` / `make dev-api` / `make dev-scheduler` 一键启动
- [ ] `docs/worklog/` 每阶段有对应记录文件
- [ ] `docs/project.md` 全部章节填充完毕（与五阶段绑定填）
- [ ] `CLAUDE.md` 顶部添加强制阅读引用 `docs/project.md`
- [ ] `.claude/memory/MEMORY.md` 加 `docs/project.md` 链接
- [ ] `example.env` 与新 `AppConfig` 字段一致
- [ ] `docker-compose.{local,dev-server,test,prod}.yml` 与新进程模型一致
- [ ] `scheduler` service 配置 `stop_grace_period: 60s`
- [ ] 抽样验证：随机挑 3 条 `docs/project.md` 规范，对应代码确实落地

---

## 渐进展开规则

每完成一阶段（合并 + dev 部署 + 24h 观察）后：

1. 调用 `superpowers:writing-plans` skill，输入"基于 spec v3.6 §6 阶段 N 展开详细 plan，参考阶段 N-1 的实际产出（路径/接口/命名）"
2. 生成 `docs/superpowers/plans/2026-04-30-refactor-stageN-<topic>.md`
3. 在本 Master plan 的"五阶段 Plan 文件"表格里更新链接

---

## 现在开始

**进入 Stage 1：基础设施层** — 详见 `docs/superpowers/plans/2026-04-30-refactor-stage1-infrastructure.md`
