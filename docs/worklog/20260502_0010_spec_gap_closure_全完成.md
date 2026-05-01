# Spec Gap Closure 全部完成（2026-05-02 00:10）

## TL;DR

✅ **重构 spec v3.7 100% 对齐**, 11 个差距项全清, 测试 **443 passed + 2 skipped 全绿**。

## 任务交付

| Task | 内容 | 工作量 | commit | merge |
|---|---|---|---|---|
| 5 | services/event_bus.py 平铺 | S | 656ebb2 | 050c80d |
| 6 | services/ws_manager.py 拆出 | S | e5a2bf0 | 69196e6 |
| 8 | common/pagination.py 提级 | S | dbdfaf2 | f858439 |
| 9 | _auto_log + ContextFilter 抽查 | S | c87d9ae | 594beb1 |
| 11 | example.env + MEMORY.md 同步 | S | 42693a0 | 500b967 |
| 7 | spec v1 偏差标注 + project.md 同步 | S | a2ecb49 | 4c77759 |
| 3 | alembic 迁入 src/db/ | M | 3fb293f | e8c5b5c |
| 4 | core/indicators + core/trace 落地 | M | d05ac32 | a26e98c |
| 1 | 独立 src/schemas/ 顶层目录 | L | 6a437a5 | afad8bf |
| 2 | task_dispatcher + Redis BRPOP + recover_orphans | L | 0726c11 | e9239d3 |

(Task 10 = start_scheduler 主循环已并入 Task 2)

## 关键变更

### Task 2 (task_dispatcher) 落地细节
- 新 model `models/task_request.py` (status: PENDING/RUNNING/SUCCESS/FAILED, 含 attempts/started_at/finished_at/error_message/trading_mode)
- migration `20260501_235824_bebb346066f0_add_task_requests_table.py` (alembic revision 命令生成, 手填 upgrade/downgrade + status CHECK + 3 索引)
- `cruds/task_request_crud.py` 暴露 create_pending / mark_running (CAS) / mark_success / mark_failed / find_orphan_running
- `services/task_dispatcher.py` 含 enqueue / dispatch_loop / recover_orphans + 注册表 HANDLERS dict + register_handler 装饰器
- handler `MANUAL_CLOSE_ALL` 注册 (调 manual_ops 同步实现)
- `scripts/start_scheduler.py` 主线程改 recover_orphans + dispatch_loop
- 4 个新单测 (enqueue / 成功流转 / 失败流转 / orphan 恢复)

### Task 1 (schemas/ 顶层) 落地细节
- 新建 `src/schemas/` 含 7 个领域文件: auth.py / user.py / symbol_config.py / runtime_config.py / command.py / risk_event.py
- 11 个 Pydantic 入参类迁过来 + 8 个改名 (xxxRequest → xxxCreate, xxxUpdate 保留)
- HTTP 响应 JSON 零变更 (响应仍是手写 dict, schema 只用于入参校验)
- 未填充 position/trade/order/decision/report/account/event 等领域 (当前 controller 直接返 dict, 无需收纳)

### Task 4 (core/indicators + core/trace) 落地细节
- `core/indicators/calculators.py`: IndicatorValues dataclass + compute_indicators() + safe_float() + MIN_CANDLES_FOR_FULL_INDICATORS
- `core/trace/trace_id.py`: generate_trace_id(decision_id, symbol, action) 32 位 SHA256 截断
- `services/insight/indicators/computer.py` 仅保留 IO + DB; `services/execution/order_executor.py` 改 import core 版

### Task 3 (alembic 迁入) 关键修复
- `script_location = %(here)s/migrations` (脱离 cwd, 相对 alembic.ini)
- `prepend_sys_path = ../..` (backend/ 进 sys.path)
- 全部调用方加 `-c src/db/alembic.ini` (conftest / scripts / 5 个集成测试 / 单测)

## 累计统计

| 维度 | 数字 |
|---|---|
| 11 个 task 全部 ✅ | 100% spec v3.7 对齐 |
| 新增 commit | 10 个分支 + 10 个 merge |
| 新建文件 | 17 (schemas 8 + core 4 + task_dispatcher 5) |
| 删除/改名文件 | 13 (alembic 9 + event_bus 1 + pagination 2 + 1 shim) |
| 测试基线 | 439 → 443 passed (Task 2 加 4 个), 2 skipped 不变 |
| 红线达标率 | 100% (每 task 完成都验证全绿才 merge) |

## 现状

- spec v3.7 全部章节落地 (含 §3-§10 + 附录)
- spec 文件本身 §3.1 加注 v1 实施偏差汇总
- `docs/project.md` 项目宪法与代码同步
- `.claude/memory/MEMORY.md` 顶部链 project.md
- `example.env` 9 子配置类字段全到位

## 真·剩余

- dev 24h 观察 (老板亲自验证)
- 真实业务场景下用 task_dispatcher (controller 提任务的真实路径; 当前只在 scheduler 注册 handler, controller 暂未切异步入队)
