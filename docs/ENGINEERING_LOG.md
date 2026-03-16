# AlphaPilot Engineering Log

> 记录项目推进过程中的工程性变更，尤其是自动执行的低风险收口工作。
> 目的不是替代 git 历史，而是让人快速看懂：做了什么、为什么做、怎么验证的。

---

## 2026-03-17 — Phase 3 收口（低风险自动推进）

### 背景

本轮工作的目标不是继续扩展高风险实盘交易逻辑，而是把 Phase 3 已经存在的实现收口到更稳定、更可验证、更可部署的状态。

原则：

- 不修改高风险实盘交易决策/执行语义
- 优先处理测试、迁移、部署一致性、控制台保护、文档对齐
- 每个实现块完成后都执行验证，并 commit + push

---

### 实现块 1：配置与迁移链稳定化

**提交**：`ad9032b`  
**commit message**：`fix: stabilize config and migrations for phase 3 closeout`

#### 做了什么

1. 为 `backend/src/shared/config.py` 补充测试/健康检查可用的安全占位默认值
2. 修正 `backend/migrations/env.py`：优先使用 Alembic 显式传入的数据库 URL
3. 新增首个 Alembic 初始迁移：`backend/migrations/versions/20260316_0001_init_schema.py`
4. 调整 `backend/alembic.ini`，收掉 `path_separator` 相关告警
5. 更新 `CLAUDE.md` 和 `.claude/memory/project_phase2_services.md`，把“Phase 3 待实现”改成更接近真实代码状态的描述

#### 为什么做

之前仓库存在以下问题：

- 健康检查和测试依赖真实环境变量，导致回归脆弱
- migration 测试没有真正对应的迁移脚本
- Alembic 测试配置和应用配置读取顺序不合理
- 文档状态落后于代码实际状态

#### 验证

- `cd backend && .venv/bin/pytest -q tests/api/test_health.py tests/integration/test_migrations.py`
- `cd backend && .venv/bin/pytest -q`

结果：backend 测试恢复通过。

---

### 实现块 2：Dashboard 危险操作保护与环境提示

**提交**：`6eeb8e1`  
**commit message**：`feat: harden dashboard actions and environment warnings`

#### 做了什么

1. 前端环境标签统一为 `local / dev / test / prod`
2. 将 `/ap` 或 `mainnet` 视为高风险环境，在控制台顶部显示红色警示 Banner
3. 对危险操作增加额外保护：
   - 手动平仓：确认提示中显示币种与风险环境
   - 一键平仓：高风险环境下要求输入 `CLOSE ALL`
   - 风控解除：确认提示中显示事件描述
4. README 增补“当前开发状态”，说明项目已从“骨架搭建”转向“Phase 3 收口 / 稳态化 / 回归验证”

#### 为什么做

前端控制台已经具备危险操作能力，但环境感知和保护还不够强，尤其在主路径或 mainnet 场景下需要更醒目的提示和更高的误触门槛。

#### 验证

- `cd frontend && npm run build`
- `cd backend && .venv/bin/pytest -q`

结果：前端 build 通过，backend 回归通过。

---

### 实现块 3：统一运行入口到 Alembic 迁移链

**提交**：`ebd2f4b`  
**commit message**：`refactor: unify runtime database setup around alembic`

#### 做了什么

1. `backend/scripts/start.sh` 不再直接运行 `create_tables.py`，改为统一执行 `upgrade_db.py`
2. `backend/scripts/init_db.py` 不再临时生成 migration，而是直接执行现有迁移链到 `head`
3. 更新文档说明，明确运行入口已经统一到 Alembic 链路

#### 为什么做

此前运行时 schema 创建存在两条路径：

- SQLAlchemy `create_all`
- Alembic migration

这会造成：

- 本地/线上 schema 来源不一致
- 难以追踪 schema 变更
- 长期维护风险高

这次改动的目标是把 schema 生命周期统一到 migration 管理。

#### 验证

- `cd backend && .venv/bin/pytest -q`
- `bash -n backend/scripts/start.sh`

结果：backend 测试通过，脚本语法正常。

---

### 实现块 4：补回归测试护栏

**提交**：`74920ac`  
**commit message**：`test: add regression coverage for config and migration scripts`

#### 做了什么

1. 在 `backend/tests/unit/test_config.py` 增加测试，验证在禁用环境注入时仍有安全默认值
2. 新增 `backend/tests/unit/test_db_scripts.py`，验证 `init_db.py` / `upgrade_db.py` 的行为是统一执行 `alembic upgrade head`
3. 在 `backend/tests/integration/test_migrations.py` 增加 `orders.trace_id` 唯一约束测试，保护幂等性基础设施

#### 为什么做

前面几轮修改已经让配置和迁移行为更稳定，但如果没有护栏，后面很容易被改回去。测试补齐后，这些低风险工程约束就变成可验证的项目规则。

#### 验证

- `cd backend && .venv/bin/pytest -q tests/unit/test_config.py tests/unit/test_db_scripts.py tests/integration/test_migrations.py`
- `cd backend && .venv/bin/pytest -q`

结果：backend 全量测试达到 **57 passed**。

---

### 额外说明

- 曾尝试启动 Codex 做后台低风险收口，但首次命令参数写法有误，任务未成功启动。
- 该失败已记录，不影响已完成的实现块和已推送提交。
- 后续若继续使用后台 coding agent，需先验证命令格式与 workdir 传参。

---

## 文档约定

从本次开始，凡是以下类型的工作，都应同步记录到本文件：

- 自动推进的低风险实现块
- 迁移/部署/测试体系收口
- 不直接体现在 PRD 里的工程性修复
- 需要让“明天来看的人”快速理解上下文的阶段性变化

建议记录模板：

- 做了什么
- 为什么做
- 如何验证
- 对应 commit
