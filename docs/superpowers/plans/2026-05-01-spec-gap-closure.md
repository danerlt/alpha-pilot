# Spec Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans 串行执行；每 task 独立分支 + 合 main + push。

**Goal:** 把 `docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` (v3.7) 剩余 11 个差距项全部补完，对齐至 100%。

**Architecture:** 每 task 独立短分支 → 修改 → 测试 → commit → push → 合 main → 删分支。串行不并行，避免冲突。

**红线**：每 task 完成后 `cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q` 必须 ≥ 439 passed + 2 skipped。

**执行顺序**：S 任务先批量清掉建立动量 → M → L 收尾。

| 顺序 | Task | 工作量 | 分支名 |
|---|---|---|---|
| 1 | Task 5 — services/event_bus.py 平铺 | S | `refactor/event-bus-flatten` |
| 2 | Task 6 — services/ws_manager.py 拆出 | S | `refactor/ws-manager-split` |
| 3 | Task 8 — common/pagination.py 顶层 | S | `refactor/pagination-toplevel` |
| 4 | Task 9 — 抽查 _auto_log + ContextFilter | S | `chore/audit-autolog-contextfilter` |
| 5 | Task 11 — example.env + MEMORY.md | S | `chore/env-memory-sync` |
| 6 | Task 7 — 文档注解（替代代码改动） | S | `docs/api-v1-layout-note` |
| 7 | Task 3 — alembic 迁入 src/db/ | M | `refactor/alembic-into-db` |
| 8 | Task 4 — core/indicators + core/trace 搬代码 | M | `refactor/core-indicators-trace` |
| 9 | Task 1 — 独立 src/schemas/ 目录 | L | `refactor/schemas-toplevel` |
| 10 | Task 2 — task_dispatcher + Redis BRPOP | L | `feat/task-dispatcher` |

---

## Task 5 — services/event_bus.py 平铺

**Files:**
- Modify: `backend/src/services/events/bus.py` → `backend/src/services/event_bus.py` (git mv)
- Update: 所有 `from src.services.events.bus import` 调用方

**Steps:**
- [ ] `git checkout main && git pull && git checkout -b refactor/event-bus-flatten`
- [ ] `git mv backend/src/services/events/bus.py backend/src/services/event_bus.py`
- [ ] Grep `from src.services.events.bus` → 全部改 `from src.services.event_bus`
- [ ] 检查 `services/events/__init__.py` 是否有 `from .bus import xxx` 转发，如有改 `from src.services.event_bus import xxx`
- [ ] 测试 `cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q`
- [ ] commit + push + 合 main + push origin main

---

## Task 6 — services/ws_manager.py 拆出

**Files:**
- Read: `backend/src/controllers/websocket.py`
- Create: `backend/src/services/ws_manager.py`
- Modify: `backend/src/controllers/websocket.py`

**Steps:**
- [ ] 切分支 `refactor/ws-manager-split`
- [ ] 读 `controllers/websocket.py`，识别连接管理类（疑 `WSConnectionManager` 或全局 dict）
- [ ] 抽到 `services/ws_manager.py` 作为类（`add(ws)` `remove(ws)` `broadcast(payload)` `active_count()`）
- [ ] `controllers/websocket.py` 改 `from src.services.ws_manager import ws_manager`，路由内只调 ws_manager
- [ ] 测试 + commit + 合 main

---

## Task 8 — common/pagination.py 顶层

**Files:**
- Modify: `backend/src/common/schemas/pagination.py` → `backend/src/common/pagination.py` (git mv)

**Steps:**
- [ ] 切分支 `refactor/pagination-toplevel`
- [ ] `git mv backend/src/common/schemas/pagination.py backend/src/common/pagination.py`
- [ ] 如 `common/schemas/__init__.py` 有 `from .pagination` 改 `from src.common.pagination`
- [ ] 全仓 grep `from src.common.schemas.pagination` 替换
- [ ] 如 `common/schemas/` 空了删除
- [ ] 测试 + commit + 合 main

---

## Task 9 — 抽查 _auto_log + ContextFilter

**Files:**
- Read: `backend/src/common/exception/errors.py`
- Read: `backend/src/utils/log.py`
- Read: `backend/src/app.py`（middleware 注入 request_id 到 context）

**Steps:**
- [ ] 切分支 `chore/audit-autolog-contextfilter`
- [ ] 读 errors.py 确认 `AppBaseException.__init__` 内有 `logger.error(...)` + `traceback`
  - 缺则补：`import traceback; logging.getLogger(self.__class__.__module__).error("%s: %s\n%s", self.code, self.message, traceback.format_exc())`
- [ ] 读 utils/log.py 确认 `ContextFilter` 类存在并把 `request_id` 注入 LogRecord
  - 缺则补：用 `asgi-correlation-id` 的 `correlation_id.get()` + ContextFilter
- [ ] 读 logging 配置/format string 是否含 `%(request_id)s`
- [ ] 写 1-2 个单元测试佐证（如果还没有）：raise AppBaseException → caplog 有 ERROR + traceback
- [ ] 测试 + commit + 合 main

---

## Task 11 — example.env + MEMORY.md

**Files:**
- Modify: `example.env`
- Modify: `.claude/memory/MEMORY.md`

**Steps:**
- [ ] 切分支 `chore/env-memory-sync`
- [ ] 读 `backend/src/configs/app_configs.py`，列每个子配置类的字段名
- [ ] 与 `example.env` 对照，缺的补上（带 `# 描述` 注释）
- [ ] `.claude/memory/MEMORY.md` 顶部加链接：`- [项目宪法](../../docs/project.md) — 全量项目规范，新会话首读`
- [ ] commit + 合 main（无代码变更，无需跑测试，只 grep 确认 example.env 字段全 source 映射）

---

## Task 7 — 文档注解

**Files:**
- Modify: `docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md`（§3.1 加注）
- Modify: `docs/project.md`（如目录章节有提）

**Steps:**
- [ ] 切分支 `docs/api-v1-layout-note`
- [ ] 在 spec §3.1 controllers/api/v1 段后加 `> **实施偏差**：实际实现按 execution/strategy/risk/system 4 子目录分组，比 spec 平铺方案更易维护，已与老板确认。` 类似注解
- [ ] 同步更新 `docs/project.md` 第 2 章（项目结构）controllers/ 段
- [ ] commit + 合 main

---

## Task 3 — alembic 迁入 src/db/

**Files:**
- Modify: `backend/alembic.ini` → `backend/src/db/alembic.ini` (git mv)
- Modify: `backend/migrations/` → `backend/src/db/migrations/` (git mv)
- Modify: `backend/Makefile` 或 `Makefile`
- Modify: `backend/scripts/init_db.py` `backend/scripts/upgrade_db.py`（如存在）
- Modify: `backend/src/db/migrations/env.py`（搬完后路径变化）

**Steps:**
- [ ] 切分支 `refactor/alembic-into-db`
- [ ] `git mv backend/alembic.ini backend/src/db/alembic.ini`
- [ ] `git mv backend/migrations backend/src/db/migrations`
- [ ] 修 `src/db/alembic.ini`：`script_location = src/db/migrations`、`prepend_sys_path = backend`（需要相对仓库根工作）
- [ ] 修 Makefile：`alembic -c backend/src/db/alembic.ini upgrade head` 等所有命令路径
- [ ] 修 scripts/init_db.py / upgrade_db.py
- [ ] 跑一遍 `cd backend && uv run alembic -c src/db/alembic.ini current` 验证 alembic 能找到迁移
- [ ] 跑测试（测试 fixture 会触发 alembic upgrade，等于端到端验证）
- [ ] commit + 合 main

---

## Task 4 — core/indicators + core/trace

**Files:**
- Read: `backend/src/services/insight/indicators/computer.py`
- Create: `backend/src/core/indicators/calculators.py`
- Modify: `backend/src/services/insight/indicators/computer.py`（保留 DB I/O，调用 core）
- Create: `backend/src/core/trace/trace_id.py`
- Modify: 所有散落生成 trace_id 的位置（`services/execution/order_executor.py` 等）

**Steps:**
- [ ] 切分支 `refactor/core-indicators-trace`
- [ ] 读 indicators/computer.py，识别纯计算函数（ema/rsi/macd/atr/bbands/volume_ma/volatility）
- [ ] 抽到 `core/indicators/calculators.py`（无 db 依赖，输入 pandas Series/DataFrame，返回 Series 或 dict）
- [ ] computer.py 改为：取候选 K 线 → 调 calculators → 写 indicator 表
- [ ] grep `SHA256.*decision_id` 找 trace_id 生成点 → 抽到 `core/trace/trace_id.py:generate_trace_id(decision_id: int, symbol: str, action: str) -> str`
- [ ] 调用方改 `from src.core.trace.trace_id import generate_trace_id`
- [ ] 测试 + commit + 合 main

---

## Task 1 — 独立 src/schemas/ 目录

**Files:**
- Create: `backend/src/schemas/__init__.py` + 每域一个文件
- Modify: 所有 controller / service / cruds 改 import

**Steps:**
- [ ] 切分支 `refactor/schemas-toplevel`
- [ ] 列出全仓现有 Pydantic Schema 类位置（`grep -rn "class.*BaseModel"` `grep -rn "class.*Read\|class.*Create\|class.*Out"`）
- [ ] 按 model 领域归类（position/trade/decision/risk_event/report/account/user/auth/command/runtime_config）
- [ ] 创建 `src/schemas/<domain>.py` 文件，挪 Schema 类进去
- [ ] **命名规范化**：`xxxResponse` / `xxxRequest` / `xxxIn` / `xxxOut` / 自由命名 → 统一 `xxxRead` / `xxxCreate` / `xxxUpdate` / `xxxOut` / `xxxQuery`
- [ ] controllers / services 改 import 路径
- [ ] 删空的 `controllers/api/v1/.../schemas.py` 文件
- [ ] **验证响应 JSON 不变**：跑测试，所有响应断言通过
- [ ] commit + 合 main

---

## Task 2 — task_dispatcher + Redis BRPOP

**Files:**
- Create: `backend/src/models/task_request.py`
- Create: `backend/src/db/migrations/versions/<新>_add_task_request.py`（用 `alembic revision -m`）
- Create: `backend/src/cruds/task_request.py`
- Create: `backend/src/services/task_dispatcher.py`
- Modify: `backend/scripts/start_scheduler.py`
- Modify: `backend/src/services/manual_ops.py`（close-all 改用 dispatcher）
- Test: `backend/tests/unit/services/test_task_dispatcher.py`

**Steps:**
- [ ] 切分支 `feat/task-dispatcher`
- [ ] 写 model（含 enum `TaskStatus = PENDING/RUNNING/SUCCESS/FAILED`）
- [ ] `cd backend && uv run alembic -c src/db/alembic.ini revision -m "add task_request table"`，编辑 upgrade/downgrade
- [ ] 写 BaseCrud 子类
- [ ] 写 TaskDispatcher 类：`enqueue` `dispatch_loop` `recover_orphans`，handler 注册表 dict
- [ ] 实现 `MANUAL_CLOSE_ALL` handler（调 manual_ops.close_all_positions 同步实现）
- [ ] start_scheduler.py 主线程改 `dispatch_loop()`，启动前先 `recover_orphans()`
- [ ] manual_ops 暴露同步 path（保留向后兼容） + 异步 enqueue path（新）
- [ ] 写测试：enqueue → 模拟 BRPOP → handler 调用 → 状态流转
- [ ] 测试 + commit + 合 main

---

## 收尾

- [ ] 写 worklog `docs/worklog/20260502_<HHMM>_spec_gap_closure_完成.md`：列每 task commit SHA、最终测试基线、对应 spec 章节
- [ ] 更新 `docs/project.md` 第 2 章（项目结构）反映最终目录
- [ ] 更新 `.claude/memory/MEMORY.md` 加重构完成记录
