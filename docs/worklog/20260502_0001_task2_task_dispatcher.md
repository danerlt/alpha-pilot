# Task 2 — 异步任务调度体系落地 (spec §4.9.1)

## 做了什么
- 新增 `TaskRequest` model (`backend/src/models/task_request.py`),
  字段: id / task_type / payload / status / attempts / enqueued_at /
  started_at / finished_at / error_message / trading_mode + Base 公共字段。
- 用 `alembic revision` 命令生成 migration 骨架, 编辑 upgrade/downgrade
  填表定义 + status CHECK 约束 + 3 个索引:
  `backend/src/db/migrations/versions/20260501_235824_bebb346066f0_add_task_requests_table.py`
- 新增 `TaskRequestCrud` (`backend/src/cruds/task_request_crud.py`):
  `create_pending` / `mark_running` (CAS, WHERE status=PENDING) /
  `mark_success` / `mark_failed` / `find_orphan_running`。
- 新增 `TaskDispatcher` 服务 (`backend/src/services/task_dispatcher.py`):
  - `enqueue` (API 用): 写 PENDING + LPUSH redis
  - `dispatch_loop` (scheduler 主线程): BRPOP timeout=1, 路由到 handler,
    异常 mark_failed + 记 error_message
  - `recover_orphans`: 启动时把卡 RUNNING 的标 FAILED (V0.1 不重新入队)
  - `register_handler` 装饰器 + HANDLERS 注册表
  - 默认注册 `MANUAL_CLOSE_ALL` handler (调 ManualOpsService.manual_close_all)
- 改造 `backend/scripts/start_scheduler.py`:
  原 `_consume_task_queue` 占位 → 实例化 TaskDispatcher,
  先 `recover_orphans()` 再 `dispatch_loop(_stop_flag)`。
- 模型 `__init__.py` 导出 TaskRequest。

## 为什么做
spec §4.9.1 定义"前台 API 写任务行 + LPUSH redis,
scheduler 进程消费"的解耦模式; 当前完全缺失, 主循环只是空 sleep。
Task 2 是 spec gap closure 计划的最后一项。

## 测试
- 4 个新单测 `backend/tests/unit/services/test_task_dispatcher.py`:
  - `test_enqueue_writes_row_and_pushes_redis`
  - `test_dispatch_loop_runs_handler_on_success`
  - `test_dispatch_loop_marks_failed_on_handler_exception`
  - `test_recover_orphans_marks_old_running_as_failed`
- 全量: 443 passed + 2 skipped (符合红线 ≥ 443)

## 验证
```
cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q
# 443 passed, 2 skipped
```

## 不破坏老路径
controller `/api/commands/close-all` 仍走原同步 ManualOpsService;
本次只是多注册一条 dispatcher 消费路径让 scheduler 进程也能执行同等任务,
controller 暂未切换。
