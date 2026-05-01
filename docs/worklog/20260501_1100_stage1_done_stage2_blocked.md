# 老板早上好 — 重构进展 read me（2026-05-01）

## TL;DR

- ✅ **Stage 1 完成 + 合并 main**：基础设施层全部就位（utils / configs / db / common / middleware / app 提级 + 中间件栈），459 测试全绿（基线 424 → +35）。
- ⚠️ **Stage 2 主动暂停**：spec v3.6 §6 阶段 2 的核心假设"主键 String(32) UUID → BigInteger 升级"**与现实不符** —— 项目早已使用 BigInt 自增主键。继续按 spec 走会做无效改动并破坏已有 schema。
- 🔁 **附带修复了一个生产 bug**：`fix/runtime-config-routes` —— `src/app/router.py` 漏注册 runtime_config router，导致 `/api/config/runtime` 路径全 404，6 个相关测试预先就失败。已合 main。

---

## Stage 1 实际产出（已合 main）

### 新增文件结构

```
backend/src/
├── app/__init__.py            # ⭐ 提级，FastAPI 工厂在这里
├── app/app.py                 # re-export shim 兼容旧代码
├── configs/app_configs.py     # 重写，8 个子配置类多继承
├── common/
│   ├── api_response.py        # @api_response 装饰器（占位，阶段 4 用）
│   ├── events.py              # BaseEvent 占位
│   ├── exception/{errors,exception_handler}.py
│   ├── response/{response_code,response_schema}.py
│   └── schemas/pagination.py  # Paginated[T]
├── db/{engines,session}.py    # PostgreSQL 同步 engine + SessionLocal + CurrentSession
├── middleware/{request_logging,error_logging}_middleware.py
└── utils/{log,request_id,uuid,time,redis,json}.py
```

### 关键能力

- **request_id 注入**：`CorrelationIdMiddleware` + `get_uuid_without_hyphen` 生成 32 字符 hex
- **异常自动 ERROR 日志**：`AppBaseException._auto_log` 含定位 + 调用栈 + request_id + 真实子类名
- **统一响应 schema**：`Response[T]` + `response_base.success/fail`
- **全局 exception handler**：业务异常 HTTP 200 + body `success:false`；未识别 `Exception` 兜底 + traceback
- **6xxxxx 业务错误码段**：`ErrorCode.KILL_SWITCH_PAUSED / RISK_REJECTED / IDEMPOTENCY_CONFLICT / ...`
- **测试基础设施**：`conftest._silence_app_exception_autolog` + `_reset_logger_disabled_state` 解决 testcontainers 副作用

### 验证

- `pytest -q`：459 passed + 2 skipped 全绿
- `client.get("/api/health/")` 响应头 `X-Request-ID: 1574d4f3112d4b098a7f0dc1da289797`（32 hex）
- 日志含 `request_id=...` 字段
- HTTP 行为零变化，前端无感知

### Stage 1 未做（按 spec 留给阶段 4）

- 现有 routers 未迁到 `controllers/`
- `Response[T]` 未替换现有 router 返回值
- 现有 `HTTPException` 未替换为 `AppBaseException`
- 前端未升级 fetch 封装

---

## Stage 2 暂停的原因（请老板决策）

### spec 假设 vs 现实

spec v3.6 §6 阶段 2 范围写的：
> - 每个 model 第一字段为 `id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)`
> - 所有跨表关联列（`Order.position_id` 等）改 `BigInteger`
> - **`migrations/versions/` 全量删除并重建**

**现实**（grep 出来的统计）：

| 主键类型 | 表数 |
|---------|-----|
| `BigIntPk`（=`BigInteger().with_variant(Integer(), "sqlite")`） | **30** |
| `Integer` | 4（`audit_log` / `symbol_config` / `system_setting` / `user`） |

**项目早已使用 BigInt 自增主键**。Stage 2 spec 的核心动作"升级到 BigInt 自增"等于**改动一个已经正确的 schema** —— 全删 migrations + 重建 = 主动给已对的代码挖坑。

### 实际还需要做的（vs spec 写的）

| spec 写的 | 现实 | 行动 |
|----------|------|------|
| 主键升级 String → BigInt | 已经是 BigInt | ❌ **不做**（无效改动） |
| migrations/versions 全删重建 | 现有 migrations 已正确 | ❌ **不做**（破坏 dev/prod 状态） |
| `shared/models/` → `src/models/` 路径搬迁 | 真实需要 | ✅ 做 |
| 引入 `Base + TradingModeMixin` 公共字段 | 当前各 model 自定义 | ✅ 做（重构改造） |
| 引入 `cruds/base_crud.py` + 17 实体 crud | 真实需要 | ✅ 做（约 26 实体） |
| `src/schemas/` 平铺 | 当前在 `shared/schemas/`，需迁 | ✅ 做（路径搬迁） |

**有效工作量**：路径搬迁 + Base 重构 + cruds 引入。**spec 强调的"主键升级"不需要**。

### 为何不直接自己改 spec 继续推

3 个考虑：
1. 主键现实是 `BigIntPk`（含 sqlite variant），不是纯 `BigInteger` —— 是否保留 sqlite 兼容是设计决策，老板拍板更稳
2. 4 个表用 `Integer` 而不是 `BigInteger`（user / audit_log / symbol_config / system_setting）—— 是否统一到 BigInt 是设计决策
3. spec §4.2.3 写"`Base` 不含 `id`，每个 model 单独定义"，但这是配合"全部主键升级"假设的；现在主键已正确，**Base 是否应该收编 `id` 字段**值得重新讨论（统一更省样板）

---

## 老板回来需要决策的 3 件事

### 决策 1：Stage 2 范围调整

- A. **保守路径**：跳过主键改造，仅做"路径搬迁 + Base 抽公共字段 + 引入 cruds + Mixin"，**不动 migrations**
- B. **激进路径**：把 4 个 Integer 主键的表升级到 BigInteger（user / audit_log / symbol_config / system_setting），需要新增一个 alembic revision
- C. **彻底重构**：照 spec 删 migrations 重建（**不推荐**，dev 数据全丢且无收益）

我推荐 **A**。

### 决策 2：`Base` 是否收编 `id` 字段

spec 说每个 model 自定义 id。但既然主键已经统一是 `BigIntPk + autoincrement=True`（30/30 表一致），**收编到 Base 反而减少样板**。建议：

- 推荐 **更新 spec：Base 收编 `id` 字段**，新表不必重复声明
- 4 个 Integer 主键表保留 override（或在决策 1 选 B 时统一）

### 决策 3：`BigIntPk` 的 sqlite variant 保留？

`BigIntPk = BigInteger().with_variant(Integer(), "sqlite")` 让单测用 sqlite in-memory 时 fallback 到 Integer。这是**已有的工程取舍**，spec 没有体现。是否：

- A. 保留 `BigIntPk`（与现状一致，spec 加注释）
- B. 删 sqlite variant，改要求所有测试用真 PostgreSQL（提高门槛但更"生产一致"）

我推荐 **A**（保留现状，写进 docs/project.md）。

---

## 我没有继续 Stage 3-5 的原因

- Stage 3 业务层重组依赖 Stage 2 的 cruds/ 接口 —— Stage 2 没定型，Stage 3 必返工
- Stage 4 响应/异常切换是 breaking change，**必须老板 review 前端**
- Stage 5 进程拆分 + docker-compose 改造需要 dev 部署 24h 观察，**必须老板在场**

---

## 老板回来后的建议节奏

1. 看本 read me（5 分钟）
2. 拍板上述 3 个决策（10 分钟）
3. 我根据决策更新 spec v3.7 + 重写 Stage 2 plan（30 分钟）
4. 我执行 Stage 2（半天）
5. 重复 Stage 3 / 4 / 5

总周期估计：1-2 周，每阶段独立 dev 24h 观察。

---

## 当前 git 状态

```
main: 09de314（Stage 1 已合）
worktree: 干净
分支：refactor/stage1-infra 已删除
PR 状态：自动 ff merge，未走 PR review（dev 环境无 staging）
```

dev server 部署已自动触发（按 CLAUDE.md 规则）；老板回来可在 dev 环境验证 X-Request-ID 是否生效。
