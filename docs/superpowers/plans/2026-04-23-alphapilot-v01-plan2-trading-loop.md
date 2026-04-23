# AlphaPilot V0.1 Plan 2 — Trading Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Plan 1 foundation 之上落地 V0.1 的完整交易闭环——从 K 线拉取 → 指标计算 → 因子合成 → Regime 分类 → AI Pipeline（Prompt → Decision → Review）→ Guard 校验 → 下单执行 → 止损止盈监控。端到端在 Testnet 上跑通一次完整决策循环。

**Architecture:** 按 spec §2 的四平面组织。所有新模块放到 `src/insight/`、`src/strategy/`、`src/execution/` 下，**不修改既有 `src/services/` 旧模块**（旧模块会在 Plan 5 cleanup 时删除）。模块间只通过 Plan 1 的事件契约（`EventEnvelope` + `OutboxWriter`）通信，不直接 import。

**Tech Stack:** Python 3.12、SQLAlchemy 2.x、Pydantic v2、pandas + pandas-ta、anthropic / openai SDK、Plan 1 已有的 `BinanceAdapter` / `EventBus` / `OutboxWriter` / `InboxGuard`。

**Spec reference:** `docs/superpowers/specs/2026-04-21-alphapilot-v1-system-design.md` §4（Strategy Plane）、§5（Factor & Insight）、§6（Execution Core）。

---

## File Structure

```
backend/src/
├── insight/                          ← Factor & Insight Plane
│   ├── __init__.py
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── computer.py              IndicatorComputer（pandas-ta 包装 + DB 写入）
│   ├── factors/
│   │   ├── __init__.py
│   │   ├── registry.py              FactorRegistry + FactorContext
│   │   ├── catalog/
│   │   │   ├── __init__.py
│   │   │   ├── trend_strength.py
│   │   │   ├── momentum_quality.py
│   │   │   ├── volume_confirmation.py
│   │   │   ├── volatility_regime.py
│   │   │   ├── breakout_validity.py
│   │   │   └── pullback_opportunity.py
│   │   └── computer.py              FactorComputer（遍历 registry 写 factor_snapshots）
│   ├── regime/
│   │   ├── __init__.py
│   │   └── classifier.py            基于 factor 值的阈值分类
│   └── experience/
│       ├── __init__.py
│       └── retriever.py             ExperienceRetriever v1（标签检索）
│
├── strategy/                         ← Strategy Intelligence Plane
│   ├── __init__.py
│   ├── proposal.py                  DecisionProposal dataclass
│   ├── router.py                    StrategyRouter（V0.1 单路由）
│   └── ai_trader/
│       ├── __init__.py
│       ├── llm_client.py            LLMClient Protocol + ClaudeClient + OpenAIClient
│       ├── prompt_composer.py       PromptComposer
│       ├── decision_solver.py       DecisionSolver
│       ├── review_critic.py         ReviewCritic（规则版）
│       └── pipeline.py              AITraderPipeline 编排三段
│
├── execution/                        ← Execution Core（Plan 1 已有 exchange/，本 Plan 加 account/guard/orders/monitor）
│   ├── account/
│   │   ├── __init__.py
│   │   └── state.py                 AccountStateService
│   ├── market/
│   │   ├── __init__.py
│   │   └── data.py                  MarketDataService
│   ├── guard/
│   │   ├── __init__.py
│   │   └── execution_guard.py       10 条规则链
│   ├── orders/
│   │   ├── __init__.py
│   │   └── executor.py              OrderExecutor（trace_id 幂等）
│   └── monitor/
│       ├── __init__.py
│       └── position_monitor.py      秒级止损/止盈/熔断
│
└── workers/
    ├── strategy_pipeline.py          15 分钟定时触发 Pipeline
    └── position_monitor_worker.py    10 秒定时触发监控（区别于既有 position_monitor.py）

backend/tests/
├── unit/
│   ├── insight/
│   │   ├── test_indicator_computer.py
│   │   ├── factors/
│   │   │   ├── test_registry.py
│   │   │   └── test_catalog.py     （6 个因子逐一断言）
│   │   ├── test_regime_classifier.py
│   │   └── test_experience_retriever.py
│   ├── strategy/
│   │   ├── test_proposal.py
│   │   ├── test_router.py
│   │   └── ai_trader/
│   │       ├── test_llm_client.py
│   │       ├── test_prompt_composer.py
│   │       ├── test_decision_solver.py
│   │       ├── test_review_critic.py
│   │       └── test_pipeline.py
│   └── execution/
│       ├── test_account_state.py
│       ├── test_market_data.py
│       ├── test_execution_guard.py
│       ├── test_order_executor.py
│       └── test_position_monitor.py
└── integration/
    └── test_strategy_pipeline_e2e.py  端到端：testcontainers + mock Binance + mock LLM → 完整一次循环
```

---

## Conventions

1. **模块间只通过事件通信**：每个 Part C/D 的 handler 完成业务后用 `OutboxWriter.record(session, ...)` 发事件；消费端用 `InboxGuard.claim(session, event_id)` 做幂等。
2. **LLM 调用经 `LLMClient` 抽象**，不直接 `import anthropic` / `import openai`，便于 mock + 以后加本地模型。
3. **所有数据写入都走 `account_id` 参数**，不依赖任何"默认 tenant"。模型 FK 对 `accounts.id`。
4. **所有跑测试命令从 repo 根执行**：`cd E:/ai/alpha-pilot && backend/.venv/Scripts/python.exe -m pytest backend/tests/... -v`
5. **每个 Task 结束：git commit + git push**（CLAUDE.md 规则）。
6. **不修改 `src/services/` 旧模块**；新实现独立开发，最后 Plan 5 或独立 cleanup PR 再移除旧代码。
7. **既有的 `workers/strategy_loop.py` 和 `workers/position_monitor.py` 不动**；本 Plan 新增 `workers/strategy_pipeline.py` 和 `workers/position_monitor_worker.py`。Plan 5 / cleanup 时再切换并移除旧的。
8. **Plan 2 不接通 APScheduler**：新 worker 的 `run_once()` 是可独立调用的函数，由测试和后续 Plan 5 的 `app.py` lifespan 决定怎么调度。

---

## Part A: Insight Plane（Factor + Regime + Experience）

本部分产出：给定 symbol/timeframe，系统能从 DB 里拉 K 线 → 算指标 → 算因子 → 分类 regime → 写 DB + 发事件。独立可测（Mock `BinanceAdapter`），不依赖 AI。

### Task A1: IndicatorComputer

**目标：** 给定 K 线 DataFrame，算 13 个指标（EMA20/50/200、RSI、MACD 三线、ATR、BB 三线、volume_ma、volatility）并写入 `indicator_snapshots` 表。复用既有 `services/indicators/calculator.py` 的算法，但用新命名（`src/insight/indicators/computer.py`）、新接口（输入 `account_id` + `symbol` + `timeframe`，从 `candles` 表拉数据）。

**Files:**
- Create: `backend/src/insight/__init__.py`
- Create: `backend/src/insight/indicators/__init__.py`
- Create: `backend/src/insight/indicators/computer.py`
- Create: `backend/tests/unit/insight/__init__.py`
- Create: `backend/tests/unit/insight/test_indicator_computer.py`

**Key interface:**

```python
# src/insight/indicators/computer.py
from dataclasses import dataclass

@dataclass
class IndicatorValues:
    ema20: float | None
    ema50: float | None
    ema200: float | None
    rsi: float | None
    macd: float | None
    macd_signal: float | None
    macd_hist: float | None
    atr: float | None
    bb_upper: float | None
    bb_middle: float | None
    bb_lower: float | None
    volume_ma: float | None
    volatility: float | None

    def is_valid_for_trading(self) -> bool:
        """True iff ATR 和 EMA20 都算出来了（risk 管理的最低要求）。"""
        return self.atr is not None and self.ema20 is not None


class IndicatorComputer:
    def __init__(self, session: Session):
        self._session = session

    def compute(
        self,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
    ) -> tuple[IndicatorValues, int | None]:
        """从 candles 表拉最近 210 根 K 线，算指标，UPSERT 到 indicator_snapshots。
        返回 (values, snapshot_id)。snapshot_id 为 None 表示 K 线不够没写。"""
```

**Steps:**
- [ ] A1.1 写失败测试 `test_indicator_computer.py`：
  - 准备 SQLite in-memory + `Base.metadata.create_all`
  - 插入 250 根合成 K 线（线性上涨 trend）
  - 调 `IndicatorComputer(session).compute(account_id=1, ..., symbol="BTCUSDT", timeframe="1h")`
  - 断言返回的 `IndicatorValues.ema20 < ema50 is False`（上涨趋势下 EMA20 在 EMA50 上方）、`atr > 0`、`rsi > 50`
  - 断言 `indicator_snapshots` 表有一行，`account_id=1`
  - 覆盖路径：K 线少于 20 根时返回全 None + `snapshot_id=None`
- [ ] A1.2 运行测试见红
- [ ] A1.3 实现 `IndicatorComputer`，算法可参考既有 `services/indicators/calculator.py`
- [ ] A1.4 运行测试见绿
- [ ] A1.5 commit `foundation(plan2): add IndicatorComputer (insight plane)` + push

**Note:** 既有 `services/indicators/calculator.py` 不要删；新实现独立开发。

---

### Task A2: Factor Registry + 6 个预置因子

**目标：** 按 spec §5.2，实现 `FactorRegistry` + 6 个预置因子类。每个因子实现 `compute(ctx) -> float`，取值归一化到 `[-1, 1]`（情绪/趋势类）或 `[0, 1]`（质量类）。

**Files:**
- Create: `backend/src/insight/factors/__init__.py`
- Create: `backend/src/insight/factors/registry.py`
- Create: `backend/src/insight/factors/catalog/__init__.py`
- Create: 6 个因子类文件（见下）
- Create: `backend/tests/unit/insight/factors/__init__.py`
- Create: `backend/tests/unit/insight/factors/test_registry.py`
- Create: `backend/tests/unit/insight/factors/test_catalog.py`

**Key interfaces:**

```python
# src/insight/factors/registry.py
from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from src.insight.indicators.computer import IndicatorValues


@dataclass
class FactorContext:
    """Inputs every factor computes against."""
    candles: pd.DataFrame  # OHLCV with at least 210 rows
    indicators: IndicatorValues


class Factor(Protocol):
    name: str
    version: int
    def compute(self, ctx: FactorContext) -> float: ...


class FactorRegistry:
    def __init__(self):
        self._factors: dict[str, Factor] = {}

    def register(self, factor: Factor) -> None: ...
    def all_active(self) -> list[Factor]: ...
    def get(self, name: str) -> Factor | None: ...


# Default registry populated at module import time.
DEFAULT_REGISTRY = FactorRegistry()
```

**6 个因子（每个一个文件，`catalog/*.py`）：**

| 因子 | name | 范围 | 公式（概要） |
|------|------|------|------|
| 趋势强度 | `trend_strength` | [-1, 1] | `sign(EMA20-EMA50) * min(1, |EMA20-EMA50| / (ATR * 2))`；EMA 排列 20>50>200 额外 +0.2，反向 -0.2 |
| 动量质量 | `momentum_quality` | [-1, 1] | `tanh(MACD_hist / ATR) * weight(RSI)`；RSI 在 50±10 区间 weight=1，外面衰减 |
| 放量确认 | `volume_confirmation` | [0, 1] | `min(1, current_volume / volume_ma - 1)` clamp 到 [0, 1]（缩量为 0） |
| 波动率区间 | `volatility_regime` | [0, 1] | `(BB_width / close) / ATR_pct_median`，标准化到 [0, 1]；0=low, ~0.5=normal, 1=high |
| 突破有效性 | `breakout_validity` | [-1, 1] | 价格突破 BB upper 且量能放大 且未被吞没 → 正；突破后回落破 middle → 负 |
| 回撤机会 | `pullback_opportunity` | [0, 1] | 上升趋势中回踩 EMA20 未破 EMA50 时 >0，其他 =0 |

**Steps:**
- [ ] A2.1 写 `test_registry.py`：register / get / all_active 基础行为
- [ ] A2.2 写 `test_catalog.py`：对每个因子用合成 `FactorContext`（强上涨 / 盘整 / 混乱三种场景）断言取值方向和范围
- [ ] A2.3 运行测试见红
- [ ] A2.4 实现 `registry.py` + 6 个因子类 + 在 `DEFAULT_REGISTRY` 注册
- [ ] A2.5 运行测试见绿
- [ ] A2.6 commit `foundation(plan2): add factor registry + 6 preset factors` + push

---

### Task A3: FactorComputer

**目标：** 遍历 `DEFAULT_REGISTRY` 的所有激活因子，对给定 `(account_id, symbol, timeframe, open_time)` 上下文计算并 UPSERT 到 `factor_snapshots`。

**Files:**
- Create: `backend/src/insight/factors/computer.py`
- Create: `backend/tests/unit/insight/factors/test_computer.py`

**Key interface:**

```python
# src/insight/factors/computer.py
class FactorComputer:
    def __init__(self, session: Session, registry: FactorRegistry = DEFAULT_REGISTRY):
        ...

    def compute_and_store(
        self,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        indicators: IndicatorValues,
        candles_df: pd.DataFrame,
    ) -> tuple[dict[str, float], int]:
        """算所有因子 → UPSERT factor_snapshots → 返回 (factors_dict, snapshot_id)。"""
```

**Steps:**
- [ ] A3.1 写 `test_computer.py`：插合成数据 → 调 `compute_and_store` → 断言 `factor_snapshots` 表里有 1 行，`factors_json` 包含 6 个 key（每个因子一个）
- [ ] A3.2 运行见红
- [ ] A3.3 实现
- [ ] A3.4 运行见绿
- [ ] A3.5 commit `foundation(plan2): add FactorComputer` + push

---

### Task A4: RegimeClassifier

**目标：** 基于因子值（不再直接用指标）分类 regime，按 spec §5.3 的阈值规则。

规则：
```
trending_up   ← trend_strength > 0.6  && volatility_regime != "high" (< 0.8)
trending_down ← trend_strength < -0.6 && volatility_regime != "high"
ranging       ← |trend_strength| < 0.3 && volatility_regime < 0.4
chaotic       ← volatility_regime >= 0.8 || breakout_validity < -0.5
```

阈值来自 `risk_profiles.regime_thresholds_json`（可学习），如果没配置则用 V0.1 硬编码默认。

**Files:**
- Create: `backend/src/insight/regime/__init__.py`
- Create: `backend/src/insight/regime/classifier.py`
- Create: `backend/tests/unit/insight/test_regime_classifier.py`

**Key interface:**

```python
# src/insight/regime/classifier.py
@dataclass
class RegimeResult:
    regime: Literal["trending_up", "trending_down", "ranging", "chaotic"]
    confidence: float  # [0, 1]，距阈值越远置信度越高


class RegimeClassifier:
    def __init__(self, thresholds: dict | None = None):
        """thresholds=None → use V0.1 defaults."""

    def classify(self, factors: dict[str, float]) -> RegimeResult: ...

    def classify_and_store(
        self,
        *,
        session: Session,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        open_time: datetime,
        factor_snapshot_id: int,
        factors: dict[str, float],
    ) -> RegimeResult:
        """分类 + UPSERT 到 regime_snapshots 表。"""
```

**Steps:**
- [ ] A4.1 写 `test_regime_classifier.py`：
  - 四种 regime 各一个测试（手写因子值）
  - 阈值覆盖（自定义 thresholds vs 默认）
  - `classify_and_store` 写 DB
- [ ] A4.2 运行见红
- [ ] A4.3 实现
- [ ] A4.4 运行见绿
- [ ] A4.5 commit `foundation(plan2): add RegimeClassifier (factor-based)` + push

---

### Task A5: ExperienceRetriever v1

**目标：** V0.1 版——按 `(account_id, symbol, regime, strategy_mode)` 标签从 `experiences` 表取最近 N 笔（按 `created_at desc`）。V0.2 再加 pgvector。

**Files:**
- Create: `backend/src/insight/experience/__init__.py`
- Create: `backend/src/insight/experience/retriever.py`
- Create: `backend/tests/unit/insight/test_experience_retriever.py`

**Key interface:**

```python
# src/insight/experience/retriever.py
@dataclass
class ExperienceSummary:
    """Plain struct for prompt injection."""
    symbol: str
    regime_at_open: str | None
    strategy_mode: str | None
    pnl_pct: float | None
    exit_reason: str | None


class ExperienceRetriever:
    def __init__(self, session: Session):
        self._session = session

    def top_k(
        self,
        *,
        account_id: int,
        symbol: str,
        regime: str | None = None,
        strategy_mode: str | None = None,
        limit: int = 5,
    ) -> list[ExperienceSummary]:
        """ORDER BY created_at DESC LIMIT limit，可选按 regime / strategy_mode 过滤。"""
```

**Steps:**
- [ ] A5.1 写 `test_experience_retriever.py`：
  - 插 10 条 `experiences`（混合 symbol/regime）
  - 断言 `top_k(symbol="BTCUSDT", limit=3)` 返回最近 3 条且都是 BTCUSDT
  - 断言 regime 过滤正确
- [ ] A5.2 运行见红
- [ ] A5.3 实现
- [ ] A5.4 运行见绿
- [ ] A5.5 commit `foundation(plan2): add ExperienceRetriever v1 (tag-based)` + push

---

## Part B: Strategy Plane（AIT Pipeline）

本部分产出：给定市场上下文（indicators + factors + regime + experience）→ 产出 `DecisionProposal`。Mock LLM + 真实 Prompt 模板 + 规则版 Review。

### Task B1: DecisionProposal dataclass

**目标：** 按 spec §4.1 统一契约，所有策略路径的唯一对外产物。

**Files:**
- Create: `backend/src/strategy/__init__.py`
- Create: `backend/src/strategy/proposal.py`
- Create: `backend/tests/unit/strategy/__init__.py`
- Create: `backend/tests/unit/strategy/test_proposal.py`

**Key definition:**

```python
# src/strategy/proposal.py
from pydantic import BaseModel, Field
from typing import Literal

class DecisionProposal(BaseModel):
    account_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "HOLD"]
    confidence: float = Field(ge=0.0, le=1.0)
    entry_type: Literal["MARKET", "LIMIT"] | None = None
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    strategy_mode: Literal[
        "ai_trend", "ai_breakout", "ai_observation",
        "program_trend", "program_breakout",
    ]
    reasoning: list[str] = Field(default_factory=list)
    risk_note: str | None = None
    # 元信息
    source: Literal["ai_trader", "program_trader", "shadow", "manual"]
    pipeline_version: str = "v0.1"
    prompt_template_id: int | None = None
    llm_model_id: str | None = None
    factor_snapshot_id: int | None = None
    parent_proposal_id: int | None = None
    is_fallback: bool = False

    @classmethod
    def fallback_hold(cls, *, account_id: int, symbol: str, timeframe: str, reason: str) -> "DecisionProposal":
        return cls(
            account_id=account_id, symbol=symbol, timeframe=timeframe,
            action="HOLD", confidence=0.0,
            strategy_mode="ai_observation",
            source="ai_trader",
            reasoning=[f"fallback: {reason}"],
            is_fallback=True,
        )
```

**Steps:**
- [ ] B1.1 写 `test_proposal.py`：
  - 合法 OPEN_LONG 能构造
  - `confidence > 1` 抛 ValidationError
  - `action="OPEN_SHORT"` 抛（Literal 限制）
  - `fallback_hold` 返回 `is_fallback=True`、`action=HOLD`
- [ ] B1.2 运行见红
- [ ] B1.3 实现
- [ ] B1.4 运行见绿
- [ ] B1.5 commit `foundation(plan2): add DecisionProposal pydantic contract` + push

---

### Task B2: LLMClient 抽象 + Claude/OpenAI 实现

**目标：** 统一 LLM 调用接口，让 DecisionSolver 不感知底层 SDK 差异；mock 单测无需装 anthropic。

**Files:**
- Create: `backend/src/strategy/ai_trader/__init__.py`
- Create: `backend/src/strategy/ai_trader/llm_client.py`
- Create: `backend/tests/unit/strategy/ai_trader/__init__.py`
- Create: `backend/tests/unit/strategy/ai_trader/test_llm_client.py`

**Key interface:**

```python
# src/strategy/ai_trader/llm_client.py
from dataclasses import dataclass
from typing import Protocol

@dataclass
class LLMResult:
    raw_text: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    model: str = ""
    provider: str = ""


class LLMTimeout(Exception):
    """LLM 调用超时，调用方回退 HOLD。"""


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str, max_tokens: int = 1024, timeout_s: int = 30) -> LLMResult: ...


class ClaudeClient:
    def __init__(self, api_key: str, model: str):
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, *, system, user, max_tokens=1024, timeout_s=30) -> LLMResult:
        import time
        start = time.monotonic()
        try:
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                timeout=timeout_s,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise LLMTimeout(str(e)) from e
            raise
        latency_ms = int((time.monotonic() - start) * 1000)
        text = msg.content[0].text if msg.content else ""
        usage = msg.usage if hasattr(msg, "usage") else None
        tokens = (usage.input_tokens + usage.output_tokens) if usage else None
        return LLMResult(
            raw_text=text, tokens_used=tokens, latency_ms=latency_ms,
            model=self._model, provider="claude",
        )


class OpenAIClient:
    # 类似结构，调 openai.OpenAI.chat.completions.create(...)
    ...


class MockLLMClient:
    """测试用；按 canned_response 回。"""
    def __init__(self, canned_response: str, model: str = "mock-model"):
        self._canned = canned_response
        self._model = model

    def complete(self, **kwargs) -> LLMResult:
        return LLMResult(
            raw_text=self._canned, tokens_used=42, latency_ms=10,
            model=self._model, provider="mock",
        )
```

**Steps:**
- [ ] B2.1 写 `test_llm_client.py`：MockLLMClient 返回 canned、tokens 和 latency 非空
- [ ] B2.2 运行见红
- [ ] B2.3 实现三个类
- [ ] B2.4 运行见绿
- [ ] B2.5 commit `foundation(plan2): add LLMClient protocol + Claude/OpenAI/Mock implementations` + push

---

### Task B3: PromptComposer

**目标：** 从 `prompt_templates` 表取 active 模板 → 注入 `{indicators, factors, regime, position, account, experience}` → 渲染 system/user prompts → 写 `proposal_drafts` 表 → 返回 `(proposal_draft_id, system, user)`。

**Files:**
- Create: `backend/src/strategy/ai_trader/prompt_composer.py`
- Create: `backend/tests/unit/strategy/ai_trader/test_prompt_composer.py`

**Key interface:**

```python
# src/strategy/ai_trader/prompt_composer.py
@dataclass
class PromptContext:
    account_id: int
    symbol: str
    timeframe: str
    current_price: float
    indicators: dict[str, float | None]
    factors: dict[str, float]
    regime: str
    open_position: dict | None  # None = no position; else {quantity, entry_price, sl, ...}
    account_snapshot: dict      # {available_usdt, daily_pnl, daily_pnl_pct}
    recent_experience: list[dict]  # [ExperienceSummary.dict(), ...]


@dataclass
class PromptBundle:
    proposal_draft_id: int
    template_id: int
    system: str
    user: str
    context_hash: str  # SHA-256 of canonicalized context dict; used for dedup


class PromptComposer:
    def __init__(self, session: Session):
        self._session = session

    def compose(self, ctx: PromptContext) -> PromptBundle:
        """1. 查 active prompt_templates WHERE name='ait_default' AND active=true
           2. str.Template 替换变量（简单 `${var}` 占位，避免 Jinja 依赖）
           3. 生成 context_hash
           4. INSERT proposal_drafts row
           5. 返回 PromptBundle
        """
```

**V0.1 预置模板 seed**（在单测 fixture 里准备即可，实际 seed 放 Plan 5）：

```
name: "ait_default"
version: 1
system_template:
  "你是 AlphaPilot 的 AI 交易决策员。任务是在受限策略框架下，为 ${symbol} (${timeframe}) 输出一个严格的 JSON 决策。
   动作只能是 OPEN_LONG / CLOSE_LONG / HOLD。
   必须附带 stop_loss 价格；risk_reward_ratio >= 1.5。
   仅当市场 regime 在 {trending_up, ranging} 且因子信号清晰时才开仓；CHAOTIC 一律 HOLD。
   输出字段：action, confidence(0-1), entry_type, entry_price, stop_loss, take_profit,
   position_size_pct(0-0.2), strategy_mode, reasoning(list of strings), risk_note。"
user_template:
  "当前价格: ${current_price}
   指标: ${indicators_json}
   因子: ${factors_json}
   市场状态: ${regime}
   当前持仓: ${open_position_json}
   账户: ${account_snapshot_json}
   最近经验: ${recent_experience_json}
   请输出 JSON。"
```

**Steps:**
- [ ] B3.1 写 `test_prompt_composer.py`：
  - Fixture：SQLite + 插 1 条 active `prompt_templates` + 调 `compose(ctx)`
  - 断言返回 `PromptBundle.system` 包含 `BTCUSDT`、`user` 包含具体指标
  - 断言 `proposal_drafts` 表里多了 1 行，`context_hash` 长度 64（SHA-256 hex）
  - 空 `recent_experience` 也能渲染（null JSON）
- [ ] B3.2 运行见红
- [ ] B3.3 实现
- [ ] B3.4 运行见绿
- [ ] B3.5 commit `foundation(plan2): add PromptComposer` + push

---

### Task B4: DecisionSolver

**目标：** 调 LLMClient → 解析 JSON → 构造 `DecisionProposal` → 写 `ai_decisions` 表；任何异常（timeout、JSON 错、字段缺、非法 action、缺 stop_loss）统一兜底 HOLD。

**Files:**
- Create: `backend/src/strategy/ai_trader/decision_solver.py`
- Create: `backend/tests/unit/strategy/ai_trader/test_decision_solver.py`

**Key interface:**

```python
# src/strategy/ai_trader/decision_solver.py
class DecisionSolver:
    def __init__(self, session: Session, llm: LLMClient):
        self._session = session
        self._llm = llm

    def solve(
        self,
        *,
        prompt_bundle: PromptBundle,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        factor_snapshot_id: int,
    ) -> tuple[DecisionProposal, int]:
        """1. llm.complete(system, user)
           2. parse JSON
           3. 校验: action in {OPEN_LONG, CLOSE_LONG, HOLD}
              stop_loss 必填（非 HOLD）
              position_size_pct in [0, MAX_POSITION_SIZE_PCT]
           4. 写 ai_decisions（包括 raw_output, llm_provider, llm_model, tokens_used, latency_ms,
              proposal_draft_id, factor_snapshot_id, source='ai_trader', is_fallback=False/True)
           5. 返回 (proposal, decision_id)
           任一步异常 → 兜底 HOLD + is_fallback=True，raw_output 保留错误信息。"""
```

**JSON 解析：**
- LLM 输出的 code fence（```json ... ```）要剥掉
- 用 `json.loads` 而不是 eval
- Pydantic 的 `DecisionProposal(**data)` 做二次校验

**Steps:**
- [ ] B4.1 写 `test_decision_solver.py`（6+ 测试）：
  - 正常 JSON → 返回 OPEN_LONG proposal、`ai_decisions` 行 `is_fallback=False`
  - 包 code fence 的 JSON → 也能解析
  - 无效 JSON → fallback HOLD
  - `action="OPEN_SHORT"` → fallback（不支持做空）
  - 缺 stop_loss → fallback
  - `LLMTimeout` → fallback
  - `position_size_pct > 0.2` → fallback
- [ ] B4.2 运行见红
- [ ] B4.3 实现（用 `MockLLMClient` 注入各种场景）
- [ ] B4.4 运行见绿
- [ ] B4.5 commit `foundation(plan2): add DecisionSolver with fallback-HOLD for all failure paths` + push

---

### Task B5: ReviewCritic（V0.1 规则版）

**目标：** 对 `DecisionSolver` 产出的 proposal 做二次校验（不调 LLM，V0.1 纯规则）：
- SL/TP 合理性：`|entry - sl| / ATR` 应该在 [0.5, 5.0] 区间
- R/R 比：`|tp - entry| / |entry - sl| >= min_rr_ratio`（默认 1.5）
- Regime 一致性：`regime == "trending_down" && action == "OPEN_LONG"` → 拒绝
- 近期经验矛盾：最近 3 笔 pnl_pct 负且相同 `strategy_mode` → 警告但不拒绝（V0.1 宽松，V0.2 加强）

**Files:**
- Create: `backend/src/strategy/ai_trader/review_critic.py`
- Create: `backend/tests/unit/strategy/ai_trader/test_review_critic.py`

**Key interface:**

```python
# src/strategy/ai_trader/review_critic.py
@dataclass
class ReviewResult:
    result: Literal["approve", "adjust", "reject"]
    adjustments: dict | None = None  # if adjust: new SL/TP
    notes: str = ""


class ReviewCritic:
    def __init__(self, session: Session, *, min_rr_ratio: float = 1.5,
                 sl_atr_min_mult: float = 0.5, sl_atr_max_mult: float = 5.0):
        ...

    def review(
        self,
        *,
        proposal: DecisionProposal,
        decision_id: int,
        regime: str,
        atr: float,
        recent_experience: list[ExperienceSummary],
    ) -> ReviewResult:
        """写 decision_reviews 表后返回结果。"""
```

**Steps:**
- [ ] B5.1 写 `test_review_critic.py`（6+ 测试覆盖每条规则：pass/fail 两路 × 规则数）
- [ ] B5.2 运行见红
- [ ] B5.3 实现
- [ ] B5.4 运行见绿
- [ ] B5.5 commit `foundation(plan2): add ReviewCritic (rule-based V0.1)` + push

---

### Task B6: AITraderPipeline

**目标：** 串起 PromptComposer → ExperienceRetriever → DecisionSolver → ReviewCritic 四步，内部同步执行，每步失败直接返回 fallback HOLD。

**Files:**
- Create: `backend/src/strategy/ai_trader/pipeline.py`
- Create: `backend/tests/unit/strategy/ai_trader/test_pipeline.py`

**Key interface:**

```python
# src/strategy/ai_trader/pipeline.py
@dataclass
class PipelineInput:
    account_id: int
    trading_mode: str
    symbol: str
    timeframe: str
    current_price: float
    indicators: dict[str, float | None]
    factors: dict[str, float]
    regime: str
    open_position: dict | None
    account_snapshot: dict
    factor_snapshot_id: int
    atr: float  # 给 ReviewCritic 用


class AITraderPipeline:
    def __init__(
        self, session: Session, *,
        composer: PromptComposer,
        retriever: ExperienceRetriever,
        solver: DecisionSolver,
        critic: ReviewCritic,
    ):
        ...

    def run(self, inp: PipelineInput) -> DecisionProposal:
        """
        1. retriever.top_k → experience
        2. composer.compose(ctx) → bundle
        3. solver.solve(bundle) → (proposal, decision_id)
        4. critic.review(proposal, decision_id, regime, atr, experience) → result
        5. 按 result 调整 proposal:
           - approve → 返回原 proposal
           - adjust → 应用 adjustments（更新 SL/TP）后返回
           - reject → 返回 fallback HOLD，关联 decision_id / parent_proposal_id
        任一步 Exception → fallback HOLD 并记录到 ai_decisions
        """
```

**Steps:**
- [ ] B6.1 写 `test_pipeline.py`：
  - 正常路径：MockLLM 返回合法 JSON → approve → 返回 OPEN_LONG
  - Solver 兜底：MockLLM 返回乱码 → pipeline 返回 fallback HOLD
  - Critic reject：SL 过近 → pipeline 返回 fallback HOLD，parent_proposal_id 指向 solver 的 decision
  - Critic adjust：TP 不合理 → pipeline 返回带调整后 TP 的 proposal
- [ ] B6.2 运行见红
- [ ] B6.3 实现
- [ ] B6.4 运行见绿
- [ ] B6.5 commit `foundation(plan2): add AITraderPipeline orchestration` + push

---

### Task B7: StrategyRouter

**目标：** V0.1 所有组合都路由到 AI Trader。留接口为 V0.2+ 加 Program Trader / Shadow 做准备。

**Files:**
- Create: `backend/src/strategy/router.py`
- Create: `backend/tests/unit/strategy/test_router.py`

**Key interface:**

```python
# src/strategy/router.py
class StrategyAdapter(Protocol):
    def propose(self, inp: PipelineInput) -> DecisionProposal: ...


class StrategyRouter:
    def __init__(self, ai_trader: StrategyAdapter):
        self._ai_trader = ai_trader
        # V0.2+ 会加 program_trader 字段

    def decide(self, inp: PipelineInput) -> DecisionProposal:
        """V0.1: 所有输入 → ai_trader.propose(inp)。写 audit_logs 记录路由决策。"""
```

（`AITraderPipeline.run` 已符合 `StrategyAdapter` Protocol 的 `propose` 签名，改个方法名即可 —— 或保留 `run`，Router 调 `ai_trader.run(inp)`。选后者，少一次重命名。）

**Steps:**
- [ ] B7.1 写 `test_router.py`：构造 mock AITrader 返回固定 proposal，断言 Router 原样返回；audit_logs 多一行
- [ ] B7.2-B7.5 TDD + commit

---

## Part C: Execution Core（Market + Account + Guard + Executor + Monitor）

### Task C1: MarketDataService

**目标：** 用 Plan 1 `BinanceAdapter` 拉 K 线，UPSERT 到 `candles` 表，通过 `OutboxWriter` 发 `candle.closed` 事件。

**Files:**
- Create: `backend/src/execution/market/__init__.py`
- Create: `backend/src/execution/market/data.py`
- Create: `backend/tests/unit/execution/test_market_data.py`

**Key interface:**

```python
# src/execution/market/data.py
class MarketDataService:
    def __init__(
        self, session: Session, adapter: ExchangeAdapter,
        outbox: OutboxWriter | None = None,
    ):
        ...

    def fetch_and_store(
        self,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        trace_id: str,
        limit: int = 300,
    ) -> int:
        """1. adapter.get_klines(...) → list[Kline]
           2. UPSERT candles（ON CONFLICT DO UPDATE 用 Postgres insert().on_conflict_do_update）
              sqlite 测试环境用普通 INSERT + IntegrityError 兜底
           3. 对每根 K 线 outbox.record(CandleClosed) — 注意 outbox 可选（测试时 None 跳过）
           4. 返回写入条数"""
```

**Steps:**
- [ ] C1.1 写 `test_market_data.py`：用 mock adapter 返回 5 根 Kline；断言 candles 表有 5 行，`OutboxWriter` mock 被调 5 次
- [ ] C1.2-C1.5 TDD + commit

---

### Task C2: AccountStateService

**目标：** 拉 Binance 账户余额/持仓 → 写 `account_snapshots` 表 + 更新 `positions.current_price`。

**Files:**
- Create: `backend/src/execution/account/__init__.py`
- Create: `backend/src/execution/account/state.py`
- Create: `backend/tests/unit/execution/test_account_state.py`

**Key interface:**

```python
# src/execution/account/state.py
class AccountStateService:
    def __init__(self, session: Session, adapter: ExchangeAdapter):
        ...

    def sync_snapshot(
        self, *, account_id: int, trading_mode: str,
    ) -> AccountSnapshot:
        """1. adapter.get_balance("USDT") → total/available
           2. 查 positions 表加总 unrealized_pnl
           3. 查 trades 表加总今天的 daily_pnl
           4. INSERT account_snapshots
           5. 返回最新 snapshot（SQLAlchemy 对象）"""

    def get_current_balance_usdt(self, account_id: int, trading_mode: str) -> float: ...
    def get_daily_pnl(self, account_id: int, trading_mode: str) -> tuple[float, float]: ...
```

**Steps:**
- [ ] C2.1-C2.5 TDD + commit（mock adapter.get_balance 返回固定值；插合成 Position/Trade；断言 snapshot 字段）

---

### Task C3: ExecutionGuard

**目标：** 按 spec §6.3 的 10 条规则链校验 proposal。复用既有 `services/execution_guard/guard.py` 的规则，但接口换成：输入 `DecisionProposal`、返回 `GuardDecision`。

**Files:**
- Create: `backend/src/execution/guard/__init__.py`
- Create: `backend/src/execution/guard/execution_guard.py`
- Create: `backend/tests/unit/execution/test_execution_guard.py`

**Key interface:**

```python
# src/execution/guard/execution_guard.py
@dataclass
class GuardDecision:
    result: Literal["PASS", "REJECT", "DEGRADE"]
    reason: str
    modified_action: Literal["HOLD"] | None = None  # for DEGRADE


class ExecutionGuard:
    def __init__(
        self, session: Session, *,
        risk_profile: RiskProfile,  # 注入，由调用方从 DB 取
    ):
        ...

    def check(
        self,
        *,
        proposal: DecisionProposal,
        current_price: float,
        regime: str,
        available_usdt: float,
        daily_pnl: float,
        daily_pnl_pct: float,
        atr: float,
        review_rejected: bool = False,
    ) -> GuardDecision:
        """10 条规则按顺序短路：
        1. 日亏损 ≤ -max_daily_loss_pct → REJECT circuit_breaker
        2. 连续亏损 ≥ max_consecutive_losses → REJECT circuit_breaker
        3. 可用 USDT 不足购买 position_size_pct × balance → REJECT
        4. OPEN_LONG 且已有同币仓位 → REJECT already_open
        5. position_size_pct > max_position_size_pct → REJECT oversize
        6. 单笔风险 = |entry - sl| / entry × size > max_single_risk_pct → REJECT
        7. SL 与当前价距离 < 0.5×ATR 或 > 5×ATR → REJECT sl_out_of_range
        8. R/R 比 < min_rr_ratio → REJECT poor_rr
        9. CHAOTIC regime + OPEN_LONG → DEGRADE HOLD
        10. review_rejected=True → REJECT review_reject
        11. PASS
        每次调用都写 risk_events 审计条（result=PASS 也写，便于追溯）。
        """
```

**Steps:**
- [ ] C3.1 写 `test_execution_guard.py`（~12 测试，覆盖每条规则 pass/fail）
- [ ] C3.2-C3.5 TDD + commit

---

### Task C4: OrderExecutor

**目标：** `open_long(proposal, decision_id)` / `close_long(position, reason, decision_id=None)`。trace_id = `SHA256(decision_id:symbol:action)` 首 32 字符，查 `orders.trace_id` UNIQUE 做幂等。下单后 `sync_fill()` 一次，写 `orders` + `positions`。

**Files:**
- Create: `backend/src/execution/orders/__init__.py`
- Create: `backend/src/execution/orders/executor.py`
- Create: `backend/tests/unit/execution/test_order_executor.py`

**Key interface:**

```python
# src/execution/orders/executor.py
class OrderExecutor:
    def __init__(
        self, session: Session, adapter: ExchangeAdapter,
        outbox: OutboxWriter | None = None,
    ):
        ...

    def open_long(
        self, *, proposal: DecisionProposal, decision_id: int,
        account_id: int, trading_mode: str, trace_id: str | None = None,
    ) -> tuple[Order, Position] | None:
        """1. compute trace_id if None
           2. 查 orders where trace_id == trace_id：已存在→返回既有订单（幂等）
           3. compute quantity = available_usdt × position_size_pct / current_price
              向下 round 到 symbol 精度（V0.1 简单保留小数点后 8 位）
           4. adapter.submit_order(OrderRequest(..., client_order_id=trace_id))
           5. 写 orders（status=FILLED, filled_quantity, avg_fill_price）
           6. 写 positions（status=open, entry_price=avg_fill_price, sl, tp）
           7. outbox.record(OrderSubmitted, OrderFilled, PositionOpened)
           8. commit
           9. 返回 (order, position)
           失败：写 orders status=FAILED + OrderFailed 事件，返回 None"""

    def close_long(
        self, *, position: Position, reason: str,
        decision_id: int | None = None,
        account_id: int, trading_mode: str,
    ) -> Trade | None:
        """类似：submit SELL → sync fill → 更新 position status=closed + 写 trades
        + TradeClosed / PositionClosed 事件。"""
```

**Steps:**
- [ ] C4.1 写 `test_order_executor.py`：
  - 用 `MockExchangeAdapter`（不发真实请求）
  - 成功开仓路径
  - 幂等：重复调 `open_long` 同一 decision_id 只写一条 orders
  - 失败路径：adapter 抛 ExchangeTemporarilyUnavailable（with_retry 已重试过）→ 最终 OrderFailed
  - close_long 写 trades + 更新 position
- [ ] C4.2-C4.5 TDD + commit

---

### Task C5: PositionMonitor

**目标：** 10 秒循环 `run_once()`：
1. 刷新所有 `positions.status=open` 的 `current_price` + `unrealized_pnl`
2. 检查止损：`current_price <= stop_loss` → `OrderExecutor.close_long(reason="stop_loss")`
3. 检查止盈：`current_price >= take_profit` → `OrderExecutor.close_long(reason="take_profit")`
4. 检查日亏损熔断：`daily_pnl_pct <= -max_daily_loss_pct` → 写 `risk_events CIRCUIT_BREAKER_TRIGGERED` + 事件

**Files:**
- Create: `backend/src/execution/monitor/__init__.py`
- Create: `backend/src/execution/monitor/position_monitor.py`
- Create: `backend/tests/unit/execution/test_position_monitor.py`

**Key interface:**

```python
# src/execution/monitor/position_monitor.py
@dataclass
class MonitorResult:
    prices_updated: int
    stop_loss_closed: list[int]    # position ids
    take_profit_closed: list[int]
    circuit_breaker_triggered: bool


class PositionMonitor:
    def __init__(
        self, session: Session, adapter: ExchangeAdapter,
        executor: OrderExecutor,
        account_service: AccountStateService,
        outbox: OutboxWriter | None = None,
    ):
        ...

    def run_once(self, *, account_id: int, trading_mode: str,
                 max_daily_loss_pct: float = 0.03) -> MonitorResult: ...
```

**Steps:**
- [ ] C5.1 写 `test_position_monitor.py`：
  - 无持仓：`prices_updated=0`
  - SL 触发：插 Position with SL=90, ticker=85 → close 被调用
  - TP 触发：类似
  - 熔断：daily_pnl_pct=-0.04 → circuit_breaker_triggered=True + risk_events 新增
- [ ] C5.2-C5.5 TDD + commit

---

## Part D: Pipeline 编排

### Task D1: strategy_pipeline worker

**目标：** 一个 `run_once(db, account_id)` 函数，按 `account_id × symbol × timeframe` 遍历走完 A→B→C：
1. MarketDataService.fetch_and_store
2. IndicatorComputer.compute
3. FactorComputer.compute_and_store
4. RegimeClassifier.classify_and_store
5. 检查熔断：circuit_breaker 未解除 → skip
6. AccountStateService.sync_snapshot
7. 查 open_position
8. StrategyRouter.decide(PipelineInput) → DecisionProposal
9. ExecutionGuard.check → GuardDecision
10. 按 Guard 结果：PASS+OPEN_LONG → OrderExecutor.open_long；PASS+CLOSE_LONG → close_long；DEGRADE/REJECT → 只发 decision.rejected 事件

**Files:**
- Create: `backend/src/workers/strategy_pipeline.py`
- Create: `backend/tests/integration/test_strategy_pipeline.py`（unit scope 但含多依赖）

**Key interface:**

```python
# src/workers/strategy_pipeline.py
def run_strategy_pipeline_once(
    *,
    db: Session,
    account_id: int,
    adapter: ExchangeAdapter,
    llm_client: LLMClient,
    symbols: list[str],
    timeframes: list[str],
    outbox: OutboxWriter | None = None,
) -> dict:
    """返回 summary {symbol_tf: result}，result.action 可能是 OPEN/CLOSE/HOLD/REJECT。
    所有异常内部吃掉 + 写 audit_logs，避免一轮循环被一个币种卡住。"""
```

**Steps:**
- [ ] D1.1 写 `test_strategy_pipeline.py`：
  - MockExchangeAdapter + MockLLMClient 返回 canned OPEN_LONG
  - 运行 1 次，断言：candles 多了 N 行、indicator_snapshots 有 1 行、factor_snapshots 有 1 行、regime_snapshots 有 1 行、ai_decisions 有 1 行、orders 有 1 行、positions status=open 有 1 行
  - Mock LLM 返回乱码时：ai_decisions `is_fallback=True`、orders 为空
- [ ] D1.2-D1.5 TDD + commit

---

### Task D2: position_monitor worker

**目标：** 把 Task C5 的 `PositionMonitor.run_once` 包成可被外部（APScheduler 或测试）调度的函数。

**Files:**
- Create: `backend/src/workers/position_monitor_worker.py`（注意：不覆盖既有 `position_monitor.py`）
- Create: `backend/tests/integration/test_position_monitor_worker.py`

**Key interface:**

```python
# src/workers/position_monitor_worker.py
def run_position_monitor_once(
    *, db, account_id, trading_mode, adapter, max_daily_loss_pct=0.03,
    outbox: OutboxWriter | None = None,
) -> MonitorResult: ...
```

**Steps:** 和 C5 测试共用 fixture 即可，这个任务的实质是"把组件装配起来 + 给 Plan 5 的 lifespan 提供入口"。

---

### Task D3: End-to-End 集成测试

**目标：** `test_strategy_pipeline_e2e.py`：testcontainers Postgres + Redis + mock Binance + mock LLM，跑完一次完整 pipeline，校验：
- 所有表都有期待的行
- Outbox 发了 7+ 类事件，Shuttle 搬到 Streams 后能被 consume
- 重复跑 2 次（同一 decision_id）trace_id 幂等 → orders 不会重复

**Files:**
- Create: `backend/tests/integration/test_strategy_pipeline_e2e.py`

**Steps:**
- [ ] D3.1 写测试（约 120-150 行 fixture + 1 个主 scenario）
- [ ] D3.2 跑 → 必要时 debug 各组件集成问题
- [ ] D3.3 全绿后 commit `foundation(plan2): add E2E integration test for full strategy pipeline` + push

---

## Self-Review Checklist

执行 Plan 2 后：

- [ ] 所有 20 个 Task 绿灯 + commit + push
- [ ] Plan 2 结束时 pytest 全量 ≈ 250+ passed，无退化
- [ ] Alembic head 无变化（Plan 2 不加新表）
- [ ] `src/insight/`、`src/strategy/`、`src/execution/` 目录结构与 spec §2.3 对齐
- [ ] 所有新模块遵循"不 import 其他平面"原则，只通过 DecisionProposal / 事件契约通信
- [ ] 兜底 HOLD 路径（spec §4.2）在 DecisionSolver、AITraderPipeline 都覆盖
- [ ] Guard 10 条规则每条都有单测
- [ ] OrderExecutor trace_id 幂等有专项单测
- [ ] 端到端集成测试 D3 通过

---

## Execution Handoff

**Plan 2 完成，保存到 `docs/superpowers/plans/2026-04-23-alphapilot-v01-plan2-trading-loop.md`。**

两种执行路径：

1. **Subagent-Driven（推荐）** — 遇 rate limit 时主 agent inline 接管，Plan 1 已验证该回退路径可行。
2. **Inline Execution** — 主 agent 直接做全部 20 个 Task，节省 subagent 派发成本。

**后续 Plan：**
- **Plan 3**: Control Plane + REST API（拆分 788 行 router、手动操作、KillSwitch、catchup endpoint）
- **Plan 4**: Frontend（DS 迁移、Web Shell、7 页、WebSocket）
- **Plan 5**: Pipeline 接入 APScheduler + 删除旧 `src/services/*` + 部署冒烟

V0.1 MVP 达成 = Plan 1-5 全部完成 + Testnet 连续 7 天稳定。
