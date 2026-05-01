# Spec Gap Closure — 重构补完设计

> **背景**：`docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` (v3.7) 5 阶段重构主体已合 main，整体落地度约 80%。本 spec 列出剩余 11 个差距项的**目标状态**，配套 plan `docs/superpowers/plans/2026-05-01-spec-gap-closure.md` 给出可执行步骤。

**目标**：100% 对齐重构 spec v3.7 的目录结构、命名规范、模块边界要求，为 V1 上线扫清结构性债务。

**测试基线红线**：每个 task 完成后 **439 passed + 2 skipped 全绿**；不允许下降。

---

## 11 个差距项 — 目标状态

### Task 1 — 独立 `src/schemas/` 目录（L）

**当前**：Schema 类（`xxxRead/xxxCreate/xxxUpdate/xxxOut`）散落在各 controller 文件内 / 各模块 `schemas.py`。

**目标**：
- 新建 `backend/src/schemas/` 扁平目录
- 每个领域一个文件（如 `position.py` `trade.py` `decision.py` `risk_event.py` `report.py` `account.py` `user.py` `auth.py` `command.py` `runtime_config.py`）
- 命名规范：`xxxRead`（GET 出参）/ `xxxCreate`（POST 入参）/ `xxxUpdate`（PATCH 入参）/ `xxxOut`（响应包装）/ `xxxQuery`（查询参数）
- 所有 controller / service 改从 `src.schemas.xxx` import
- **不破坏现有响应 JSON 结构**

### Task 2 — `task_request` 模型 + `services/task_dispatcher.py` + Redis BRPOP（L）

**当前**：spec §4.9.1 整套缺失。scheduler 进程 `start_scheduler.py` 主循环只有占位 `_consume_task_queue()`。

**目标**：
- 新建 `models/task_request.py`（含 `id` / `task_type` / `payload` / `status: PENDING/RUNNING/SUCCESS/FAILED` / `attempts` / `enqueued_at` / `started_at` / `finished_at` / `error_message` / `trading_mode`）
- 新建 alembic migration
- 新建 `cruds/task_request.py`
- 新建 `services/task_dispatcher.py`：
  - `enqueue(task_type, payload) -> task_id`：写 task_request 表 + LPUSH Redis list
  - `dispatch_loop()`：BRPOP → 查 task_request → 改 RUNNING → 路由到 handler → 改 SUCCESS/FAILED
  - `recover_orphans()`：scheduler 启动时把 RUNNING 但超时的标记为 FAILED 重新入队
- `start_scheduler.py` 主线程改调 `dispatch_loop()`
- Handler 注册表：当前先支持 `MANUAL_CLOSE_ALL` 一种（替换 `manual_ops.close_all_positions` 同步路径为异步入队）

### Task 3 — alembic 迁入 `src/db/`（M）

**当前**：`backend/alembic.ini` + `backend/migrations/` 在仓库根。

**目标**：
- `git mv backend/alembic.ini backend/src/db/alembic.ini`
- `git mv backend/migrations backend/src/db/migrations`
- 修 alembic.ini 的 `script_location` / `prepend_sys_path`
- 修 Makefile / scripts/ 里所有 `alembic -c ...` 路径
- 修 `migrations/env.py` 内的 import 路径

### Task 4 — `core/indicators/` + `core/trace/` 实质代码（M）

**当前**：`core/indicators/__init__.py` 空、`core/trace/` 目录空，indicators 计算器仍在 `services/insight/indicators/computer.py`。

**目标**：
- 把无状态计算逻辑从 `services/insight/indicators/computer.py` 抽到 `core/indicators/calculators.py`（纯函数：`ema(series, n)` `rsi(series, n)` `macd(series)` `atr(df, n)` `bbands(series, n)` 等）
- `services/insight/indicators/computer.py` 保留 IO + DB 写入逻辑，调用 `core.indicators.calculators`
- 新建 `core/trace/trace_id.py`：`generate_trace_id(decision_id, symbol, action) -> str`（SHA256 截断逻辑），原散落代码改 import 它
- 同样从 `services/strategy/decision_engine.py` 等处抽出

### Task 5 — `services/event_bus.py` 平铺（S）

**当前**：`services/events/bus.py`。

**目标**：`git mv services/events/bus.py services/event_bus.py`，全仓 import 替换。

### Task 6 — `services/ws_manager.py` 拆出（S）

**当前**：WebSocket 连接管理逻辑混在 `controllers/websocket.py`。

**目标**：
- 新建 `services/ws_manager.py`：抽出 `WSConnectionManager` 类（`add` `remove` `broadcast` `get_active`）
- `controllers/websocket.py` 只保留路由 + 调用 `ws_manager`
- 多 worker 兼容：通过 Redis Pub/Sub 跨 worker 广播（如果尚未实现）

### Task 7 — `controllers/api/v1` 平铺文件对齐 spec（S）

**当前**：spec §3.1 列出 `v1/reports.py` `v1/auth.py` `v1/runtime_config.py` `v1/commands.py` `v1/events_catchup.py`，但实际散在 `v1/strategy/reports.py` `v1/system/auth.py` 等子目录下。

**决策**：保留现有按域分子目录的方式（更清晰），**反向修 spec §3.1 文档说明**：
- 在 `docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` 加注：实际实现按 4 域子目录 (`execution/strategy/risk/system/`) 分组，比 spec 平铺更易维护

### Task 8 — `common/pagination.py` 顶层文件（S）

**当前**：`common/schemas/pagination.py`。

**目标**：`git mv common/schemas/pagination.py common/pagination.py`，import 替换。`common/schema.py` 不需要（无内容应该入）。

### Task 9 — 抽查 `_auto_log` + ContextFilter（S）

**目标**：
- 读 `common/exception/errors.py`：确认 AppBaseException `__init__` 自动 `logger.error(traceback.format_exc())`，未做则补
- 读 `utils/log.py`：确认 `ContextFilter` 把 `request_id` 注入 `LogRecord`，logging format 引用 `%(request_id)s`
- 不符合就修；符合就在本 task PR 加注释佐证

### Task 11 — example.env 字段对齐 + MEMORY.md 链 project.md（S）

**目标**：
- 扫 `src/configs/app_configs.py` 9 个子配置类的所有字段，与 `example.env` 对照，缺字段补到 example.env（带注释说明）
- `.claude/memory/MEMORY.md` 加一行 `[项目宪法](../../docs/project.md) — 全量项目规范，新会话先读`

---

## 不做的事

- **Task 10（start_scheduler 加 BRPOP 主循环）合并进 Task 2**，不单列
- 不引入新依赖（除 task_dispatcher 必要的 RQ 风格设计）
- 不改前端 `frontend/src/lib/api.ts` 行为
- 不改 docker-compose 服务划分

---

## 验收

- [ ] 11 项全部 ✅（Task 7 用文档注解形式 close）
- [ ] `cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q` → 至少 439 passed + 2 skipped；Task 2 引入新测试后基线相应提升
- [ ] `docs/project.md` 与代码现状一致（如目录结构变了同步更新对应章节）
- [ ] 每个 task 单独 commit + 单独合 main，每次合并前测试全绿
- [ ] 全部完成后写一份 worklog 收尾
