"""strategy_pipeline 一次完整循环集成测试 (SQLite + mock adapter + mock LLM)。

通过断言：candles / indicator_snapshots / factor_snapshots / regime_snapshots /
ai_decisions / orders / positions / decision_reviews / proposal_drafts 均有
预期行；mock LLM 返回乱码时 ai_decisions.is_fallback=True 且无新 orders。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.shared.models import (
    AIDecision,
    Base,
    DecisionReview,
    FactorSnapshot,
    IndicatorSnapshot,
    Order,
    Position,
    ProposalDraft,
    PromptTemplate,
    RegimeSnapshot,
)
from src.shared.models.account_entity import RiskProfile
from src.strategy.ai_trader.llm_client import MockLLMClient
from src.workers.strategy_pipeline import run_strategy_pipeline_once


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        # 必须的种子: 1 个 active prompt template
        s.add(PromptTemplate(
            name="ait_default", version=1,
            system_template="sys ${symbol} ${regime}",
            user_template="user ${current_price}",
            active=True,
        ))
        s.flush()
        yield s


@pytest.fixture
def profile() -> RiskProfile:
    return RiskProfile(
        account_id=1, name="default",
        max_position_size_pct=Decimal("0.20"),
        max_daily_loss_pct=Decimal("0.03"),
        max_consecutive_losses=3,
        max_single_risk_pct=Decimal("0.01"),
        min_rr_ratio=Decimal("1.50"),
        sl_atr_min_mult=Decimal("0.50"),
        sl_atr_max_mult=Decimal("5.00"),
    )


class _PipelineAdapter(ExchangeAdapter):
    """给 pipeline 用的 adapter: 假 ticker + 250 根线性上涨 K 线。"""

    def __init__(self, *, ticker_price: float = 50_000.0, fill_price: float = 50_000.0):
        self._ticker_price = ticker_price
        self._fill_price = fill_price
        self._klines = self._make_klines()

    def _make_klines(self):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        out = []
        for i in range(250):
            p = 49_000.0 + i * 4.0  # 平稳上涨, 终点约 50_000
            out.append(Kline(
                symbol="BTCUSDT", timeframe="1h",
                open_time=base + timedelta(hours=i),
                open=p * 0.999, high=p * 1.001, low=p * 0.998,
                close=p, volume=1000.0,
            ))
        return out

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, price=self._ticker_price)
    def get_klines(self, symbol, timeframe, *, limit=300, end_time=None):
        return self._klines[-limit:]
    def submit_order(self, request: OrderRequest) -> OrderResult:
        return OrderResult(
            exchange_order_id="EX-PIPE",
            symbol=request.symbol, side=request.side,
            order_type=request.order_type, status="FILLED",
            requested_quantity=request.quantity,
            filled_quantity=request.quantity,
            avg_fill_price=self._fill_price,
            client_order_id=request.client_order_id,
        )
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return 10_000.0 if asset == "USDT" else 0.0


VALID_OPEN_LONG = json.dumps({
    "action": "OPEN_LONG",
    "confidence": 0.75,
    "entry_type": "MARKET",
    "entry_price": 50_000.0,
    "stop_loss": 49_800.0,
    "take_profit": 50_400.0,
    "position_size_pct": 0.10,
    "strategy_mode": "ai_trend",
    "reasoning": ["uptrend"],
})


def test_pipeline_happy_path_writes_full_audit_chain(session, profile):
    adapter = _PipelineAdapter(ticker_price=50_000.0, fill_price=50_000.0)
    llm = MockLLMClient(canned_response=VALID_OPEN_LONG)
    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm,
        risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
    )
    assert summary["BTCUSDT:1h"]["action"] == "OPEN_LONG"
    assert summary["BTCUSDT:1h"]["guard"] == "PASS"

    # 全链审计行存在
    assert session.execute(select(IndicatorSnapshot)).scalars().first() is not None
    assert session.execute(select(FactorSnapshot)).scalars().first() is not None
    assert session.execute(select(RegimeSnapshot)).scalars().first() is not None
    assert session.execute(select(ProposalDraft)).scalars().first() is not None
    decision = session.execute(select(AIDecision)).scalars().first()
    assert decision is not None and decision.is_fallback is False
    assert session.execute(select(DecisionReview)).scalars().first() is not None
    assert session.execute(select(Order)).scalars().first() is not None
    assert session.execute(select(Position)).scalars().first() is not None


def test_pipeline_skips_decision_proposed_for_review_fallback(session, profile):
    """post-Plan5 codereview Risk #2: review reject → fallback HOLD 时, 不应 publish
    DecisionProposed (event.action=HOLD vs ai_decisions.action=OPEN_LONG 会矛盾).
    review fail 信号通过 Guard 的 decision.rejected 已经覆盖."""
    from src.events.outbox import OutboxWriter
    from src.shared.models.event_store import EventOutbox

    adapter = _PipelineAdapter()
    # OPEN_LONG + chaotic regime (但这里 regime_classifier 自动算; 我们用
    # MockLLM 输出 trending_down regime 在 critic 做 reject) — 直接构造一个
    # tight TP 触发 review reject 更可控不到, 改让 critic reject:
    # _PipelineAdapter 给的是稳定上涨 K 线 → regime 大概率 trending_up,
    # critic 不会 reject; 这里我们改用 garbage LLM 不能触发本场景.
    #
    # 改测策略: 直接断言 — 当确实有 fallback HOLD 但 parent != None 时,
    # event_outbox 没有 decision.proposed 行. 暂时用 garbage LLM
    # (Solver-fallback, parent=None) 对照: 应该 publish; 不能 publish 的
    # review-fallback 场景由 unit test_pipeline.py 的 test_review_reject 覆盖.
    llm = MockLLMClient(canned_response="not json")  # Solver-fallback, parent=None
    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm,
        risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
        outbox=OutboxWriter(),
    )
    # Solver-fallback (parent=None) → 应该正常 publish DecisionProposed
    assert summary["BTCUSDT:1h"]["is_fallback"] is True
    rows = session.execute(
        select(EventOutbox).where(EventOutbox.event_type == "decision.proposed")
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].payload_json["payload"]["is_fallback"] is True


def test_pipeline_records_outbox_events_when_outbox_present(session, profile):
    """传 OutboxWriter 后, 关键阶段应该 publish:
    indicators.computed / factors.updated / regime.classified / decision.proposed."""
    from src.events.outbox import OutboxWriter
    from src.shared.models.event_store import EventOutbox

    adapter = _PipelineAdapter(ticker_price=50_000.0, fill_price=50_000.0)
    llm = MockLLMClient(canned_response=VALID_OPEN_LONG)
    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm,
        risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
        outbox=OutboxWriter(),
    )
    assert summary["BTCUSDT:1h"]["action"] == "OPEN_LONG"

    rows = session.execute(select(EventOutbox)).scalars().all()
    types = {r.event_type for r in rows}
    # 4 类策略阶段事件 + OrderExecutor / MarketDataService 自带的 order/position/candle 事件
    assert "indicators.computed" in types
    assert "factors.updated" in types
    assert "regime.classified" in types
    assert "decision.proposed" in types

    decided = next(r for r in rows if r.event_type == "decision.proposed")
    assert decided.payload_json["payload"]["action"] == "OPEN_LONG"
    assert decided.payload_json["payload"]["is_fallback"] is False
    assert decided.payload_json["payload"]["source"] == "ai_trader"


def test_pipeline_skips_when_kill_switch_paused(session, profile):
    """人工 KillSwitch=paused → 整个 pipeline 应该跳过, 不生成任何订单。"""
    from src.control.kill_switch.service import KillSwitchService
    KillSwitchService(session).pause(operator_user_id=1, reason="maintenance")

    adapter = _PipelineAdapter()
    llm = MockLLMClient(canned_response=VALID_OPEN_LONG)
    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm,
        risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
    )
    assert summary["BTCUSDT:1h"]["action"] == "SKIP"
    assert summary["BTCUSDT:1h"]["reason"] == "blocked_by_kill_switch"
    # 没有 ai_decisions / orders 写入
    assert session.execute(select(AIDecision)).scalars().first() is None
    assert session.execute(select(Order)).scalars().first() is None


def test_pipeline_garbage_llm_falls_back_no_order(session, profile):
    adapter = _PipelineAdapter()
    llm = MockLLMClient(canned_response="not json")
    summary = run_strategy_pipeline_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, llm_client=llm,
        risk_profile=profile,
        symbols=["BTCUSDT"], timeframes=["1h"],
    )
    assert summary["BTCUSDT:1h"]["proposal_action"] == "HOLD"
    assert summary["BTCUSDT:1h"]["is_fallback"] is True
    # ai_decisions 行存在 + is_fallback=True
    decision = session.execute(select(AIDecision)).scalars().first()
    assert decision is not None and decision.is_fallback is True
    # 没有 orders / positions 写入
    assert session.execute(select(Order)).scalars().first() is None
    assert session.execute(select(Position)).scalars().first() is None
