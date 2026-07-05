# Handoff 后端 P1 — 决策流式事件 + 决策详情 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 handoff/03 §3.3 —— 策略管道各阶段发布 `decision.progress` / `decision.complete` WS 事件，并补 `GET /api/decisions/{id}` 决策详情端点（features 快照、守卫记录、review、关联订单）。

**Architecture:** 事件走既有 Outbox → EventShuttle → Redis Pub/Sub → WS 链路，只补事件类型与发射点。进度事件通过独立 `DecisionProgressEmitter`（自持 session、立即 commit）保证 LLM 调用期间前端能实时看到阶段推进，不干扰管道业务事务；`decision.complete` 与业务写同事务走 outbox 保证原子性。守卫审计行补 `decision_id` 列（alembic 迁移）使详情端点可反查守卫结果。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.x（同步 Session）/ Alembic / Redis / pytest

**关键约束（来自 docs/project.md + CLAUDE.md + 记忆）:**
- 所有内部 import `src.` 开头；同步 Session；model 字段单行；禁外键（索引可加）
- controller 只编排，业务进 service，数据访问走 cruds
- 业务异常 HTTP 200 + `success:false`；NOT_FOUND 用 `DBException(ErrorCode.NOT_FOUND)`
- alembic 迁移必须 `uv run alembic -c src/db/alembic.ini revision -m "..."` 生成骨架后填正文
- commit 中文、类型前缀、**不加 Co-Authored-By**；每 task 提交后立即 push
- 测试命令：`cd backend && uv run pytest <path> -v`（PG 5442 + Redis 6389 容器需在跑）

**阶段语义（handoff 3.3 契约）:**

| stage | 含义 | start 时点 | done 时点 |
|-------|------|-----------|----------|
| snapshot | 行情+指标+因子+regime | 拉K线前 | regime 分类完（detail: regime/confidence） |
| reasoning | prompt+LLM+review | router.decide 前 | 决策落库后（detail: decision_id/action/confidence/is_fallback） |
| guard | 执行守卫 | guard.check 前 | check 返回后（detail: result/reason） |
| verdict | 最终裁决 | —（只发 done） | guard 后立刻（detail: final_action） |
| execute | 下单 | executor 调用前（仅 PASS+可执行时） | 下单返回后 |

任一阶段抛异常 → caller 发 `{stage: 当前 stage, status: fail, detail: {error}}`。

---

### Task 1: 事件契约 DecisionProgress / DecisionComplete

**Files:**
- Modify: `backend/src/services/events/contracts.py`
- Test: `backend/tests/unit/events/test_contracts.py`

- [ ] **Step 1: 写失败测试**（追加到 test_contracts.py 末尾）

```python
def test_decision_progress_in_registry_and_roundtrip():
    from src.services.events.contracts import EVENT_TYPE_REGISTRY, DecisionProgress

    assert EVENT_TYPE_REGISTRY["decision.progress"] is DecisionProgress
    ev = DecisionProgress(
        stage="reasoning", status="done",
        symbol="BTCUSDT", timeframe="1h",
        decision_id=42, detail={"action": "OPEN_LONG", "confidence": 0.7},
    )
    parsed = DecisionProgress(**ev.model_dump())
    assert parsed.stage == "reasoning"
    assert parsed.decision_id == 42


def test_decision_complete_in_registry_and_roundtrip():
    from src.services.events.contracts import EVENT_TYPE_REGISTRY, DecisionComplete

    assert EVENT_TYPE_REGISTRY["decision.complete"] is DecisionComplete
    ev = DecisionComplete(
        decision_id=42, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", proposal_action="OPEN_LONG",
        confidence=0.72, guard_result="PASS", guard_reason="all_checks_passed",
        regime="trending_up", is_fallback=False,
        entry_price=50_000.0, stop_loss=49_000.0, take_profit=52_000.0,
        position_size_pct=0.1,
    )
    parsed = DecisionComplete(**ev.model_dump())
    assert parsed.action == "OPEN_LONG"
    assert parsed.guard_result == "PASS"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/unit/events/test_contracts.py -v`
Expected: FAIL（ImportError: cannot import name 'DecisionProgress'）

- [ ] **Step 3: 实现契约**

在 `contracts.py` 的 `DecisionRejected` 类之后（`# order.*` 注释块之前）插入：

```python
class DecisionProgress(_Event):
    """决策管道阶段进度 (handoff 3.3) — 前端 StreamingDecision 逐段点亮。"""

    event_type: ClassVar[str] = "decision.progress"
    stage: Literal["snapshot", "reasoning", "guard", "verdict", "execute"]
    status: Literal["start", "done", "fail"]
    symbol: str
    timeframe: str
    decision_id: int | None = None
    detail: dict[str, Any] | None = None


class DecisionComplete(_Event):
    """决策管道完整结束 (handoff 3.3) — 前端展开完整决策卡。"""

    event_type: ClassVar[str] = "decision.complete"
    decision_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "SKIP"]
    proposal_action: str
    confidence: float
    guard_result: Literal["PASS", "REJECT", "DEGRADE"]
    guard_reason: str
    regime: str
    is_fallback: bool = False
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = None
```

并在 `_all_event_classes()` 列表中 `DecisionDegraded, DecisionRejected,` 行后加一行：

```python
        DecisionProgress, DecisionComplete,
```

同时更新文件顶部 docstring 的 "V0.1 实际 publish 范围" 段，在 `decision.*` 行补 `decision.progress / decision.complete (strategy_pipeline worker, handoff P1)`。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/unit/events/test_contracts.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/events/contracts.py backend/tests/unit/events/test_contracts.py
git commit -m "feat(events): 新增 decision.progress / decision.complete 事件契约（handoff P1 §3.3）"
git push
```

---

### Task 2: DecisionProgressEmitter（独立 session 即时发射器）

**Files:**
- Create: `backend/src/services/events/progress.py`
- Test: `backend/tests/unit/events/test_progress_emitter.py`

**设计要点**：管道单 symbol 事务在结束时才 commit，若进度事件走同一 session，LLM 思考期间前端什么都看不到。发射器用**独立 session 立即 commit**，且**任何内部异常只记 warning 不上抛**（进度可视化绝不能影响交易主链路）。

- [ ] **Step 1: 写失败测试**

```python
"""DecisionProgressEmitter 单测 — 独立 session 即时落 outbox + 异常静默。"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base
from src.models.event_store import EventOutbox
from src.services.events.progress import DecisionProgressEmitter


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def emitter(engine):
    factory = sessionmaker(bind=engine)
    return DecisionProgressEmitter(
        session_factory=factory, account_id=1, trading_mode="testnet",
    )


def test_emit_writes_outbox_row_immediately(engine, emitter):
    emitter.emit(
        "snapshot", "start",
        symbol="BTCUSDT", timeframe="1h", trace_id="t1",
    )
    with Session(engine) as s:
        rows = s.execute(select(EventOutbox)).scalars().all()
        assert len(rows) == 1
        row = rows[0]
        assert row.event_type == "decision.progress"
        assert row.payload_json["payload"]["stage"] == "snapshot"
        assert row.payload_json["payload"]["status"] == "start"
        assert row.payload_json["trace_id"] == "t1"


def test_emit_with_decision_id_and_detail(engine, emitter):
    emitter.emit(
        "reasoning", "done",
        symbol="BTCUSDT", timeframe="1h", trace_id="t2",
        decision_id=42, detail={"action": "HOLD"},
    )
    with Session(engine) as s:
        row = s.execute(select(EventOutbox)).scalars().one()
        assert row.payload_json["payload"]["decision_id"] == 42
        assert row.payload_json["payload"]["detail"] == {"action": "HOLD"}


def test_fail_current_uses_last_started_stage(engine, emitter):
    emitter.emit("guard", "start", symbol="ETHUSDT", timeframe="1h", trace_id="t3")
    emitter.fail_current("boom")
    with Session(engine) as s:
        rows = s.execute(
            select(EventOutbox).order_by(EventOutbox.id)
        ).scalars().all()
        assert len(rows) == 2
        fail = rows[-1].payload_json["payload"]
        assert fail["stage"] == "guard"
        assert fail["status"] == "fail"
        assert fail["detail"] == {"error": "boom"}


def test_fail_current_without_prior_start_is_noop(engine, emitter):
    emitter.fail_current("boom")
    with Session(engine) as s:
        assert s.execute(select(EventOutbox)).scalars().all() == []


def test_emit_swallows_session_factory_errors(engine):
    def _broken_factory():
        raise RuntimeError("db down")

    em = DecisionProgressEmitter(
        session_factory=_broken_factory, account_id=1, trading_mode="testnet",
    )
    # 不应抛出
    em.emit("snapshot", "start", symbol="BTCUSDT", timeframe="1h", trace_id="t4")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/unit/events/test_progress_emitter.py -v`
Expected: FAIL（ModuleNotFoundError: src.services.events.progress）

- [ ] **Step 3: 实现发射器**

```python
"""DecisionProgressEmitter — decision.progress 即时发射 (handoff P1 §3.3)。

管道单 symbol 事务在末尾才 commit; 进度事件若走同一 session, LLM 调用期间
前端看不到任何推进。本发射器用独立 session 写 event_outbox 并立即 commit,
EventShuttle 下一轮即搬运到 Redis → WS。

强约束: 进度可视化绝不能影响交易主链路 —— 内部任何异常只记 warning 不上抛。
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Literal

from sqlalchemy.orm import Session

from src.services.events.contracts import DecisionProgress
from src.services.events.outbox import OutboxWriter

logger = logging.getLogger(__name__)

Stage = Literal["snapshot", "reasoning", "guard", "verdict", "execute"]
Status = Literal["start", "done", "fail"]


class DecisionProgressEmitter:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        account_id: int,
        trading_mode: str,
    ):
        self._session_factory = session_factory
        self._account_id = account_id
        self._trading_mode = trading_mode
        self._outbox = OutboxWriter()
        # (stage, symbol, timeframe, trace_id, decision_id) — fail_current 用
        self._last_started: tuple[str, str, str, str, int | None] | None = None

    def emit(
        self,
        stage: Stage,
        status: Status,
        *,
        symbol: str,
        timeframe: str,
        trace_id: str,
        decision_id: int | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        if status == "start":
            self._last_started = (stage, symbol, timeframe, trace_id, decision_id)
        try:
            session = self._session_factory()
        except Exception:
            logger.warning("progress emit skipped: session factory failed", exc_info=True)
            return
        try:
            self._outbox.record(
                session,
                aggregate_type="ai_decision",
                aggregate_id=decision_id,
                event=DecisionProgress(
                    stage=stage, status=status,
                    symbol=symbol, timeframe=timeframe,
                    decision_id=decision_id, detail=detail,
                ),
                account_id=self._account_id,
                trading_mode=self._trading_mode,
                trace_id=trace_id,
            )
            session.commit()
        except Exception:
            logger.warning("progress emit failed (non-fatal)", exc_info=True)
            try:
                session.rollback()
            except Exception:
                pass
        finally:
            try:
                session.close()
            except Exception:
                pass

    def fail_current(self, error: str) -> None:
        """当前 symbol 链路异常时, 对最后一个 start 的阶段补发 fail。"""
        if self._last_started is None:
            return
        stage, symbol, timeframe, trace_id, decision_id = self._last_started
        self.emit(
            stage, "fail",  # type: ignore[arg-type]
            symbol=symbol, timeframe=timeframe, trace_id=trace_id,
            decision_id=decision_id, detail={"error": error},
        )
        self._last_started = None
```

> 注意：`emit` 里 `status=="start"` 的记录要在 try 之外（session factory 失败也要记住 stage）。若 `OutboxWriter.record` 签名与上面不一致（以 `src/services/events/outbox.py` 实际为准），按实际签名调整。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/unit/events/test_progress_emitter.py -v`
Expected: 5 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/events/progress.py backend/tests/unit/events/test_progress_emitter.py
git commit -m "feat(events): DecisionProgressEmitter 独立会话即时发射进度事件"
git push
```

---

### Task 3: 管道埋点 + decision.complete + scheduler 接线

**Files:**
- Modify: `backend/src/workers/strategy_pipeline.py`
- Modify: `backend/src/workers/scheduler_jobs.py`（`new_strategy_pipeline_job`）
- Test: `backend/tests/integration/test_strategy_pipeline.py`（追加）

- [ ] **Step 1: 写失败测试**（追加到 test_strategy_pipeline.py，复用该文件既有 `session` / `profile` fixture 与 `_PipelineAdapter` / `MockLLMClient` / `VALID_OPEN_LONG`；若常量名不同以文件实际为准）

```python
class _FakeProgressEmitter:
    """记录 emit 调用的假发射器 — 不碰 DB。"""

    def __init__(self):
        self.calls: list[tuple[str, str, dict]] = []

    def emit(self, stage, status, **kw):
        self.calls.append((stage, status, kw))

    def fail_current(self, error: str) -> None:
        self.calls.append(("__fail__", "fail", {"error": error}))


def test_pipeline_emits_progress_stages_and_complete_event(session, profile):
    adapter = _PipelineAdapter(ticker_price=50_000.0, fill_price=50_000.0)
    llm = MockLLMClient(canned_response=VALID_OPEN_LONG)
    emitter = _FakeProgressEmitter()
    outbox = OutboxWriter()

    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm, risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
        outbox=outbox, progress_emitter=emitter,
    )
    assert summary["BTCUSDT:1h"]["action"] == "OPEN_LONG"

    seq = [(s, st) for s, st, _ in emitter.calls]
    assert seq == [
        ("snapshot", "start"), ("snapshot", "done"),
        ("reasoning", "start"), ("reasoning", "done"),
        ("guard", "start"), ("guard", "done"),
        ("verdict", "done"),
        ("execute", "start"), ("execute", "done"),
    ]
    # reasoning done 带 decision_id
    reasoning_done = [kw for s, st, kw in emitter.calls if (s, st) == ("reasoning", "done")][0]
    assert reasoning_done["decision_id"] is not None
    assert reasoning_done["detail"]["action"] == "OPEN_LONG"
    # guard done 带结果
    guard_done = [kw for s, st, kw in emitter.calls if (s, st) == ("guard", "done")][0]
    assert guard_done["detail"]["result"] == "PASS"

    # decision.complete 走 outbox（与业务同事务）
    complete_rows = [
        r for r in session.execute(select(EventOutbox)).scalars().all()
        if r.event_type == "decision.complete"
    ]
    assert len(complete_rows) == 1
    payload = complete_rows[0].payload_json["payload"]
    assert payload["action"] == "OPEN_LONG"
    assert payload["guard_result"] == "PASS"
    assert payload["regime"] in {"trending_up", "trending_down", "ranging", "chaotic"}


def test_pipeline_without_emitter_still_works(session, profile):
    """progress_emitter=None 完全兼容旧行为。"""
    adapter = _PipelineAdapter(ticker_price=50_000.0, fill_price=50_000.0)
    llm = MockLLMClient(canned_response=VALID_OPEN_LONG)
    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm, risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
    )
    assert summary["BTCUSDT:1h"]["action"] == "OPEN_LONG"
```

需在文件头补 import（若缺）：`from src.models.event_store import EventOutbox`、`from src.services.events.outbox import OutboxWriter`、`from sqlalchemy import select`。

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/integration/test_strategy_pipeline.py -v -k progress`
Expected: FAIL（TypeError: unexpected keyword argument 'progress_emitter'）

- [ ] **Step 3: 实现管道埋点**

`strategy_pipeline.py` 修改点：

a) import 区加：

```python
from src.services.events.contracts import (
    DecisionComplete,
    DecisionProposed,
    FactorsUpdated,
    IndicatorsComputed,
    RegimeClassified,
)
from src.services.events.progress import DecisionProgressEmitter
```

b) `_PipelineDeps` 追加字段：

```python
    progress: Optional[DecisionProgressEmitter] = None
```

（dataclass 有默认值字段须排在无默认值字段之后，放最后一行。）

c) `_run_one_symbol_tf` 中，`trace_id = ...` 行之后定义局部帮助函数并埋点：

```python
    def _progress(stage, status, *, decision_id=None, detail=None):
        if deps.progress is not None:
            deps.progress.emit(
                stage, status,
                symbol=symbol, timeframe=tf, trace_id=trace_id,
                decision_id=decision_id, detail=detail,
            )

    _progress("snapshot", "start")
```

d) 指标不足的早退分支改为：

```python
    if not values.is_valid_for_trading():
        _progress("snapshot", "fail", detail={"reason": "insufficient_indicators"})
        return {"action": "SKIP", "reason": "insufficient_indicators"}
```

e) regime 的 outbox.record 块之后（步骤 5 `# 5. 当前价格` 之前）：

```python
    _progress("snapshot", "done", detail={
        "regime": regime_result.regime,
        "confidence": float(regime_result.confidence),
    })
```

f) `# 8. 策略路由` 前后：

```python
    _progress("reasoning", "start")
    proposal, decision_id = deps.router.decide(pipeline_input)
    _progress("reasoning", "done", decision_id=decision_id, detail={
        "action": proposal.action,
        "confidence": float(proposal.confidence),
        "is_fallback": proposal.is_fallback,
    })
```

g) `# 9. 执行守卫` 前后：

```python
    _progress("guard", "start", decision_id=decision_id)
    guard_dec = deps.guard.check(...)  # 原调用不变
    _progress("guard", "done", decision_id=decision_id, detail={
        "result": guard_dec.result, "reason": guard_dec.reason,
    })
```

h) `# 10. 按 guard 结果路由` 改为先算 final_action 发 verdict，再执行时包 execute：

```python
    # 10. 按 guard 结果路由
    action_taken = "SKIP"
    will_execute = (
        guard_dec.result == "PASS"
        and (
            proposal.action == "OPEN_LONG"
            or (proposal.action == "CLOSE_LONG" and open_pos is not None)
        )
    )
    _progress("verdict", "done", decision_id=decision_id, detail={
        "final_action": proposal.action if will_execute else "SKIP",
        "guard_result": guard_dec.result,
    })
    if will_execute:
        _progress("execute", "start", decision_id=decision_id)
        if proposal.action == "OPEN_LONG":
            deps.executor.open_long(...)  # 原调用不变
            action_taken = "OPEN_LONG"
        else:
            deps.executor.close_long(...)  # 原调用不变
            action_taken = "CLOSE_LONG"
        _progress("execute", "done", decision_id=decision_id, detail={"action": action_taken})
```

i) return 之前发 `decision.complete`（走 db 事务内 outbox，与 decision.proposed 同模式）：

```python
    if deps.outbox is not None and decision_id is not None:
        deps.outbox.record(
            db, aggregate_type="ai_decision", aggregate_id=decision_id,
            event=DecisionComplete(
                decision_id=decision_id,
                symbol=symbol, timeframe=tf,
                action=action_taken,
                proposal_action=proposal.action,
                confidence=float(proposal.confidence),
                guard_result=guard_dec.result,
                guard_reason=guard_dec.reason,
                regime=regime_result.regime,
                is_fallback=proposal.is_fallback,
                entry_price=proposal.entry_price,
                stop_loss=proposal.stop_loss,
                take_profit=proposal.take_profit,
                position_size_pct=(
                    float(proposal.position_size_pct)
                    if proposal.position_size_pct is not None else None
                ),
            ),
            account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id,
        )
```

j) `run_strategy_pipeline_once` 签名加 `progress_emitter=None`，deps 装配加 `progress=progress_emitter`，for 循环 except 分支补：

```python
            except Exception:  # noqa: BLE001
                logger.exception("pipeline cycle failed for %s", key)
                summary[key] = {"action": "ERROR"}
                db.rollback()
                if progress_emitter is not None:
                    progress_emitter.fail_current(f"pipeline_error:{key}")
```

`progress_emitter` 参数类型标注 `Optional[DecisionProgressEmitter]`；测试传假对象没问题（duck typing）。

k) `scheduler_jobs.py::new_strategy_pipeline_job` 中 `outbox = OutboxWriter()` 之后：

```python
        progress_emitter = DecisionProgressEmitter(
            session_factory=get_session_factory(),
            account_id=1, trading_mode=settings.TRADING_MODE.value,
        )
```

`run_strategy_pipeline_once(...)` 调用补 `progress_emitter=progress_emitter,`；import 区加 `from src.services.events.progress import DecisionProgressEmitter`。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/integration/test_strategy_pipeline.py tests/unit/events/ -v`
Expected: 全 PASS（含既有用例零回归）

- [ ] **Step 5: 提交**

```bash
git add backend/src/workers/strategy_pipeline.py backend/src/workers/scheduler_jobs.py backend/tests/integration/test_strategy_pipeline.py
git commit -m "feat(pipeline): 决策链五阶段 decision.progress 埋点 + decision.complete 事件（handoff P1）"
git push
```

---

### Task 4: risk_events 补 decision_id 列（alembic）+ Guard 写入

**Files:**
- Modify: `backend/src/models/risk_event.py`
- Modify: `backend/src/services/execution/execution_guard.py`
- Create: `backend/src/db/migrations/versions/<alembic revision 生成>`（**必须用命令生成**）
- Test: `backend/tests/unit/execution/test_execution_guard.py`（追加）

- [ ] **Step 1: 写失败测试**（追加，复用该文件既有 session/profile/proposal 构造模式，以文件实际 fixture 为准）

```python
def test_guard_record_writes_decision_id_on_risk_event(session, profile):
    guard = ExecutionGuard(session, risk_profile=profile)
    proposal = _proposal_open()  # 该文件既有的 OPEN_LONG proposal 构造
    guard.check(
        proposal=proposal, trading_mode="testnet",
        current_price=50_000.0, regime="trending_up",
        available_usdt=10_000.0, daily_pnl=0.0, daily_pnl_pct=0.0,
        atr=800.0, decision_id=77,
    )
    ev = session.execute(
        select(RiskEvent).order_by(RiskEvent.id.desc())
    ).scalars().first()
    assert ev is not None
    assert ev.decision_id == 77


def test_guard_record_decision_id_nullable(session, profile):
    guard = ExecutionGuard(session, risk_profile=profile)
    proposal = _proposal_hold()  # HOLD proposal（若无现成构造则新建 action="HOLD"）
    guard.check(
        proposal=proposal, trading_mode="testnet",
        current_price=50_000.0, regime="ranging",
        available_usdt=10_000.0, daily_pnl=0.0, daily_pnl_pct=0.0,
        atr=800.0,
    )
    ev = session.execute(
        select(RiskEvent).order_by(RiskEvent.id.desc())
    ).scalars().first()
    assert ev.decision_id is None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/unit/execution/test_execution_guard.py -v -k decision_id`
Expected: FAIL（RiskEvent 无 decision_id 属性 / AssertionError）

- [ ] **Step 3: model 加字段（单行规则）**

`risk_event.py` 在 `position_id` 行后加：

```python
    decision_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
```

- [ ] **Step 4: 生成并填写 alembic 迁移（禁止手写文件）**

```bash
cd backend && uv run alembic -c src/db/alembic.ini revision -m "risk_events add decision_id"
```

编辑生成文件的正文：

```python
def upgrade() -> None:
    op.add_column("risk_events", sa.Column("decision_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_risk_events_decision_id", "risk_events", ["decision_id"])


def downgrade() -> None:
    op.drop_index("ix_risk_events_decision_id", table_name="risk_events")
    op.drop_column("risk_events", "decision_id")
```

Run: `cd backend && uv run alembic -c src/db/alembic.ini upgrade head`（对本地 dev 库；测试库由 conftest 自动 upgrade）
Expected: 迁移成功

- [ ] **Step 5: Guard 写入 decision_id**

`execution_guard.py::_record` 中 `RiskEvent(...)` 构造改为（`decision_id` 取值行移到 session.add 之前）：

```python
        decision_id = getattr(self, "_cur_decision_id", None)
        self._session.add(RiskEvent(
            account_id=proposal.account_id,
            event_type=f"GUARD_{result}",
            symbol=proposal.symbol,
            triggered_at=datetime.now(tz=timezone.utc),
            description=reason,
            resolved=(result == "PASS"),
            decision_id=decision_id,
        ))
        self._session.flush()
```

（原 outbox publish 块里的重复 `decision_id = getattr(...)` 行删除，直接用上面的局部变量。）

- [ ] **Step 6: 跑测试确认通过 + 守卫全量回归**

Run: `cd backend && uv run pytest tests/unit/execution/test_execution_guard.py -v`
Expected: 全 PASS

- [ ] **Step 7: 提交**

```bash
git add backend/src/models/risk_event.py backend/src/services/execution/execution_guard.py backend/src/db/migrations/versions/ backend/tests/unit/execution/test_execution_guard.py
git commit -m "feat(risk): risk_events 增加 decision_id 关联列，守卫审计行可反查决策"
git push
```

> 注：migrations 目录路径以 `src/db/alembic.ini` 的 `script_location` 实际配置为准（生成命令会自动放对位置）。

---

### Task 5: 决策详情 Service + CRUD 查询方法

**Files:**
- Modify: `backend/src/cruds/decision_review_crud.py`、`backend/src/cruds/risk_event_crud.py`、`backend/src/cruds/order_crud.py`、`backend/src/cruds/position_crud.py`
- Create: `backend/src/services/strategy/decision_detail.py`
- Test: `backend/tests/unit/strategy/test_decision_detail.py`

- [ ] **Step 1: 写失败测试**

```python
"""DecisionDetailService 单测 — 聚合 decision + review + guard + orders。"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.common.exception.errors import DBException
from src.models import Base
from src.models.decision import AIDecision
from src.models.decision_review import DecisionReview
from src.models.factor import FactorSnapshot
from src.models.order import Order
from src.models.risk_event import RiskEvent
from src.services.strategy.decision_detail import DecisionDetailService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed(session) -> int:
    now = datetime.now(tz=timezone.utc)
    snap = FactorSnapshot(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        open_time=now, factors_json={"trend_strength": 0.8},
    )
    session.add(snap)
    session.flush()
    d = AIDecision(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        decided_at=now, action="OPEN_LONG", confidence=0.72,
        entry_price=50_000, stop_loss=49_000, take_profit=52_000,
        position_size_pct=0.1, strategy_mode="ai_trend",
        reasoning=["EMA stack bullish"], is_fallback=False,
        factor_snapshot_id=snap.id, prompt_input={"context_hash": "h" * 64},
    )
    session.add(d)
    session.flush()
    session.add(DecisionReview(
        decision_id=d.id, reviewer_type="rule", result="approve",
    ))
    session.add(RiskEvent(
        account_id=1, trading_mode="testnet", event_type="GUARD_PASS",
        symbol="BTCUSDT", triggered_at=now, description="all_checks_passed",
        resolved=True, decision_id=d.id,
    ))
    session.add(Order(
        account_id=1, trading_mode="testnet", trace_id="x" * 32,
        symbol="BTCUSDT", side="BUY", order_type="MARKET",
        quantity=0.01, status="FILLED", ai_decision_id=d.id,
        submitted_at=now,
    ))
    session.commit()
    return d.id


def test_get_detail_aggregates_all_sections(session):
    decision_id = _seed(session)
    detail = DecisionDetailService(session).get_detail(
        decision_id, trading_mode="testnet",
    )
    assert detail["id"] == decision_id
    assert detail["action"] == "OPEN_LONG"
    assert detail["features"]["factors"] == {"trend_strength": 0.8}
    assert detail["features"]["prompt_input"]["context_hash"] == "h" * 64
    assert len(detail["reviews"]) == 1
    assert detail["reviews"][0]["result"] == "approve"
    assert len(detail["guard_events"]) == 1
    assert detail["guard_events"][0]["event_type"] == "GUARD_PASS"
    assert len(detail["orders"]) == 1
    assert detail["orders"][0]["side"] == "BUY"


def test_get_detail_not_found_raises(session):
    with pytest.raises(DBException):
        DecisionDetailService(session).get_detail(999999, trading_mode="testnet")


def test_get_detail_wrong_trading_mode_raises(session):
    decision_id = _seed(session)
    with pytest.raises(DBException):
        DecisionDetailService(session).get_detail(decision_id, trading_mode="mainnet")
```

> Order 模型必填列以 `src/models/order.py` 实际为准，缺什么补什么（如 binance_order_id 可空则不给）。

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/unit/strategy/test_decision_detail.py -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: CRUD 查询方法**（每个 crud 类内追加，遵循 `find_by_<field>` 约定）

`decision_review_crud.py`：

```python
    def find_by_decision_id(self, session: Session, decision_id: int) -> list[DecisionReview]:
        return list(session.execute(
            select(DecisionReview)
            .where(DecisionReview.decision_id == decision_id)
            .order_by(DecisionReview.id)
        ).scalars())
```

`risk_event_crud.py`：

```python
    def find_by_decision_id(self, session: Session, decision_id: int) -> list[RiskEvent]:
        return list(session.execute(
            select(RiskEvent)
            .where(RiskEvent.decision_id == decision_id)
            .order_by(RiskEvent.id)
        ).scalars())
```

`order_crud.py`：

```python
    def find_by_decision_id(self, session: Session, decision_id: int) -> list[Order]:
        return list(session.execute(
            select(Order)
            .where(Order.ai_decision_id == decision_id)
            .order_by(Order.id)
        ).scalars())
```

`position_crud.py`：

```python
    def find_by_decision_id(self, session: Session, decision_id: int) -> list[Position]:
        return list(session.execute(
            select(Position)
            .where(Position.ai_decision_id == decision_id)
            .order_by(Position.id)
        ).scalars())
```

各文件需补 `from sqlalchemy import select` 与 `from sqlalchemy.orm import Session` import。

- [ ] **Step 4: DecisionDetailService**

```python
"""DecisionDetailService — GET /api/decisions/{id} 聚合 (handoff P1 §3.3)。

聚合: ai_decisions 主行 + features(因子快照+prompt 输入) + decision_reviews
+ 守卫审计(risk_events.decision_id) + 关联 orders / positions。只读, 不 commit。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.common.exception.errors import DBException
from src.common.response.response_code import ErrorCode
from src.cruds.decision_crud import ai_decision_crud
from src.cruds.decision_review_crud import decision_review_crud
from src.cruds.factor_crud import factor_snapshot_crud
from src.cruds.order_crud import order_crud
from src.cruds.position_crud import position_crud
from src.cruds.risk_event_crud import risk_event_crud


class DecisionDetailService:
    def __init__(self, session: Session):
        self._session = session

    def get_detail(self, decision_id: int, *, trading_mode: str) -> dict:
        d = ai_decision_crud.get_or_none(self._session, decision_id)
        if d is None or d.trading_mode != trading_mode:
            raise DBException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"decision id={decision_id} not found",
            )

        factors = None
        factor_def_versions = None
        if d.factor_snapshot_id is not None:
            snap = factor_snapshot_crud.get_or_none(self._session, d.factor_snapshot_id)
            if snap is not None:
                factors = snap.factors_json
                factor_def_versions = snap.factor_def_versions_json

        reviews = decision_review_crud.find_by_decision_id(self._session, decision_id)
        guard_events = risk_event_crud.find_by_decision_id(self._session, decision_id)
        orders = order_crud.find_by_decision_id(self._session, decision_id)
        positions = position_crud.find_by_decision_id(self._session, decision_id)

        return {
            "id": d.id,
            "symbol": d.symbol,
            "timeframe": d.timeframe,
            "decided_at": d.decided_at.isoformat(),
            "action": d.action,
            "confidence": float(d.confidence) if d.confidence is not None else None,
            "entry_type": d.entry_type,
            "entry_price": float(d.entry_price) if d.entry_price is not None else None,
            "stop_loss": float(d.stop_loss) if d.stop_loss is not None else None,
            "take_profit": float(d.take_profit) if d.take_profit is not None else None,
            "position_size_pct": float(d.position_size_pct) if d.position_size_pct is not None else None,
            "strategy_mode": d.strategy_mode,
            "reasoning": d.reasoning,
            "risk_note": d.risk_note,
            "is_fallback": d.is_fallback,
            "source": d.source,
            "llm_provider": d.llm_provider,
            "llm_model": d.llm_model,
            "tokens_used": d.tokens_used,
            "latency_ms": d.latency_ms,
            "features": {
                "factor_snapshot_id": d.factor_snapshot_id,
                "factors": factors,
                "factor_def_versions": factor_def_versions,
                "prompt_input": d.prompt_input,
            },
            "reviews": [
                {
                    "id": r.id,
                    "reviewer_type": r.reviewer_type,
                    "result": r.result,
                    "adjustments": r.adjustments_json,
                    "notes": r.notes,
                }
                for r in reviews
            ],
            "guard_events": [
                {
                    "id": g.id,
                    "event_type": g.event_type,
                    "description": g.description,
                    "triggered_at": g.triggered_at.isoformat(),
                    "resolved": g.resolved,
                }
                for g in guard_events
            ],
            "orders": [
                {
                    "id": o.id,
                    "side": o.side,
                    "order_type": o.order_type,
                    "status": o.status,
                    "quantity": float(o.quantity) if o.quantity is not None else None,
                    "avg_fill_price": float(o.avg_fill_price) if o.avg_fill_price is not None else None,
                    "trace_id": o.trace_id,
                    "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
                    "filled_at": o.filled_at.isoformat() if o.filled_at else None,
                }
                for o in orders
            ],
            "position_ids": [p.id for p in positions],
        }
```

> `entry_type` / `source` 等字段若 AIDecision 模型实际没有则删掉对应行（以 `src/models/decision.py` 为准——探索确认有 entry_type、source）。

- [ ] **Step 5: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/unit/strategy/test_decision_detail.py -v`
Expected: 3 PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/cruds/ backend/src/services/strategy/decision_detail.py backend/tests/unit/strategy/test_decision_detail.py
git commit -m "feat(strategy): DecisionDetailService 聚合决策详情（features/review/守卫/订单）"
git push
```

---

### Task 6: GET /api/decisions/{id} 端点

**Files:**
- Modify: `backend/src/controllers/api/v1/strategy/decisions.py`
- Test: `backend/tests/api/test_decision_detail.py`

- [ ] **Step 1: 写失败测试**（复制 `tests/api/test_read_endpoints.py` 的 engine/authed_client fixture 模式）

```python
"""GET /api/decisions/{id} API 层测试。"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.db.session import get_db
from src.models import Base
from src.models.decision import AIDecision


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def authed_client(engine):
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    from types import SimpleNamespace

    from src.controllers.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role="user", status="active",
    )
    yield TestClient(app), engine
    app.dependency_overrides.clear()


def _seed_decision(engine) -> int:
    with Session(engine) as s:
        d = AIDecision(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT",
            timeframe="1h", decided_at=datetime.now(tz=timezone.utc),
            action="HOLD", confidence=0.5, is_fallback=False,
        )
        s.add(d)
        s.commit()
        return d.id


def test_decision_detail_returns_full_payload(authed_client):
    cli, engine = authed_client
    decision_id = _seed_decision(engine)
    r = cli.get(f"/api/decisions/{decision_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == decision_id
    assert data["action"] == "HOLD"
    assert "features" in data
    assert "reviews" in data
    assert "guard_events" in data
    assert "orders" in data


def test_decision_detail_not_found(authed_client):
    cli, _ = authed_client
    r = cli.get("/api/decisions/999999")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "400005"


def test_decision_detail_rejects_anonymous():
    cli = TestClient(app)
    r = cli.get("/api/decisions/1")
    assert r.status_code == 200
    assert r.json()["code"] == "400003"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/api/test_decision_detail.py -v`
Expected: FAIL（success=false / 404 路由不存在——实际是 FastAPI 返回 404 或校验错，按现象确认路由缺失即可）

- [ ] **Step 3: 实现端点**（decisions.py 追加）

```python
@router.get("/{decision_id}")
@api_response()
def get_decision_detail(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """决策详情: features 快照 + review + 守卫记录 + 关联订单 (要求登录)。"""
    settings = get_settings()
    return DecisionDetailService(db).get_detail(
        decision_id, trading_mode=settings.TRADING_MODE.value,
    )
```

import 区补 `from src.services.strategy.decision_detail import DecisionDetailService`。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/api/test_decision_detail.py tests/api/test_read_endpoints.py -v`
Expected: 全 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/controllers/api/v1/strategy/decisions.py backend/tests/api/test_decision_detail.py
git commit -m "feat(api): GET /api/decisions/{id} 决策详情端点（handoff P1）"
git push
```

---

### Task 7: 全量回归 + lint + worklog 收口

- [ ] **Step 1: 全量测试**

Run: `cd backend && uv run pytest -q`
Expected: ≥ 526 passed + 2 skipped，0 failed（新增用例全绿）

- [ ] **Step 2: lint + fmt**

Run: `cd backend && uv run ruff check . && uv run ruff format --check .`
Expected: 0 警告（有格式问题先 `uv run ruff format .` 再复跑测试）

- [ ] **Step 3: worklog**

写 `docs/worklog/20260703_<HHMM>_handoff后端P1_决策流式事件与详情.md`：做了什么（事件契约/发射器/管道埋点/迁移/详情端点）、为什么（handoff 3.3 契约）、如何验证（测试数字）、对应 commits。

- [ ] **Step 4: 提交收口**

```bash
git add docs/worklog/
git commit -m "docs(worklog): handoff 后端 P1 决策流式事件与详情收口记录"
git push
```

---

## Self-Review 结论

1. **规格覆盖**：handoff 3.3 两个事件类型（Task 1-3）、`GET /api/decisions/{id}` 四段内容 features/守卫逐项/reasoning/关联订单（Task 4-6，其中"守卫逐项"以 GUARD_* 审计行呈现——短路式守卫单次调用只产生一条命中记录，真正 per-check 明细在 P2 precheck 接口中随守卫重构补齐，已在 P2 范围声明）✅
2. **占位符扫描**：所有代码块完整；"以文件实际为准"仅出现在依赖既有 fixture 名/模型必填列的测试处，属执行期核对而非缺内容 ✅
3. **类型一致性**：`DecisionProgressEmitter.emit(stage, status, *, symbol, timeframe, trace_id, decision_id, detail)` 在 Task 2 定义、Task 3 管道与假发射器同签名调用；`DecisionComplete.action` Literal 含 SKIP 与 `action_taken` 取值一致 ✅
