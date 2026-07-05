"""PilotAgentService 单测 — 工具循环 / pending action / confirm 守卫 (handoff P3)。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.common.enums import PositionStatus
from src.common.exception.errors import ServiceException
from src.core.llm.client import LLMResult
from src.models import Base
from src.models.agent_invocation import AgentInvocation
from src.models.agent_pending_action import AgentPendingAction
from src.models.position import Position
from src.services.agent.pilot_agent import PilotAgentService


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _SeqLLM:
    """按顺序返回预置回复的 mock LLM。"""

    provider = "mock"

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[str] = []

    def complete(self, *, system, user, max_tokens=1024, timeout_s=30) -> LLMResult:
        self.calls.append(user)
        return LLMResult(raw_text=self._responses.pop(0), provider="mock")


class _NullAdapter:
    def get_ticker(self, symbol):
        from src.core.exchange.types import Ticker
        return Ticker(symbol=symbol, price=50_000.0)

    def get_ticker_24h(self, symbol):
        return None

    def get_futures_metrics(self, symbol):
        return None


def _svc(session, responses) -> tuple[PilotAgentService, _SeqLLM]:
    llm = _SeqLLM(responses)
    return PilotAgentService(session, llm, _NullAdapter()), llm


def _run(svc, message="现在持仓怎么样?", **kw) -> list[dict]:
    defaults = dict(user_id=1, trading_mode="testnet")
    defaults.update(kw)
    return list(svc.chat(message=message, **defaults))


def test_final_only_answer_yields_delta_and_done(session):
    svc, _ = _svc(session, [json.dumps({"final": "一切正常。"})])
    events = _run(svc)
    kinds = [e["event"] for e in events]
    assert kinds[0] == "delta" and kinds[-1] == "done"
    assert "".join(e["data"]["text"] for e in events if e["event"] == "delta") == "一切正常。"
    # 落 invocation 行
    inv = session.execute(select(AgentInvocation)).scalars().one()
    assert inv.agent_type == "pilot_chat"
    assert inv.output_json["answer"] == "一切正常。"


def test_tool_call_then_final(session):
    session.add(Position(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT",
        status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.02, entry_price=50_000.0, stop_loss=49_000.0,
        opened_at=datetime.now(tz=timezone.utc),
    ))
    session.commit()
    svc, llm = _svc(session, [
        json.dumps({"tool": "get_positions", "args": {}}),
        json.dumps({"final": "你有 1 个 BTCUSDT 多头持仓。"}),
    ])
    events = _run(svc)
    tool_events = [e for e in events if e["event"] == "tool_call"]
    assert [t["data"]["status"] for t in tool_events] == ["start", "done"]
    assert tool_events[0]["data"]["name"] == "get_positions"
    # 工具结果回填进了第二轮 prompt
    assert "BTCUSDT" in llm.calls[1]
    inv = session.execute(select(AgentInvocation)).scalars().one()
    assert inv.output_json["tools"] == ["get_positions"]


def test_propose_config_change_creates_pending_action(session):
    svc, _ = _svc(session, [
        json.dumps({"tool": "propose_config_change", "args": {
            "key": "risk.max_daily_loss_pct", "value": 0.02, "reason": "收紧风控",
        }}),
        json.dumps({"final": "已生成待确认动作, 需管理员确认。"}),
    ])
    events = _run(svc, message="帮我把日亏熔断收紧到 2%")
    done = events[-1]
    assert done["event"] == "done"
    action_id = done["data"]["pending_action_id"]
    row = session.get(AgentPendingAction, action_id)
    assert row.status == "PENDING"
    assert row.payload_json["key"] == "risk.max_daily_loss_pct"
    # 配置未被直接修改 (system_settings 无该行)
    from src.models.system_setting import SystemSetting

    assert session.execute(
        select(SystemSetting).where(SystemSetting.key == "risk.max_daily_loss_pct")
    ).scalars().first() is None


def test_propose_non_whitelisted_key_refused(session):
    svc, llm = _svc(session, [
        json.dumps({"tool": "propose_config_change", "args": {
            "key": "binance.mainnet.api_key", "value": "hack", "reason": "x",
        }}),
        json.dumps({"final": "该配置不可修改。"}),
    ])
    _run(svc, message="改 api key")
    # 无 pending 行
    assert session.execute(select(AgentPendingAction)).scalars().all() == []
    # 工具错误信息回填给了模型
    assert "白名单" in llm.calls[1]


def test_unparseable_output_treated_as_final(session):
    svc, _ = _svc(session, ["随便聊聊, 不是 JSON"])
    events = _run(svc)
    assert events[-1]["event"] == "done"
    text = "".join(e["data"]["text"] for e in events if e["event"] == "delta")
    assert "随便聊聊" in text


def test_tool_round_limit_stops(session):
    svc, _ = _svc(session, [json.dumps({"tool": "get_risk_state", "args": {}})] * 6)
    events = _run(svc)
    assert events[-1]["event"] == "done"
    text = "".join(e["data"]["text"] for e in events if e["event"] == "delta")
    assert "上限" in text


# ── confirm 守卫 (roadmap P3 验收: Agent 无法绕过 confirm 直改配置) ────────


def _pending(session, *, key="risk.max_daily_loss_pct", value=0.02) -> int:
    row = AgentPendingAction(
        action_type="config_change",
        payload_json={"key": key, "value": value, "reason": "t"},
        status="PENDING", proposed_at=datetime.now(tz=timezone.utc),
    )
    session.add(row)
    session.commit()
    return row.id


def test_confirm_applies_config_and_audits(session, monkeypatch):

    # refresh 依赖真实 runtime manager, 单测里打桩
    monkeypatch.setattr(
        "src.services.system.runtime_config.apply_runtime_settings_refresh",
        lambda *a, **kw: {},
    )
    action_id = _pending(session)
    svc, _ = _svc(session, [])
    out = svc.confirm_action(action_id=action_id, admin_user_id=9)
    assert out["status"] == "CONFIRMED"
    session.expire_all()
    row = session.get(AgentPendingAction, action_id)
    assert row.status == "CONFIRMED" and row.confirmed_by == 9
    from src.models.system_setting import SystemSetting

    setting = session.execute(
        select(SystemSetting).where(SystemSetting.key == "risk.max_daily_loss_pct")
    ).scalars().one()
    assert setting.value_json == 0.02
    from src.models.audit_log import AuditLog

    assert any(
        log.action == "agent_action_confirm"
        for log in session.execute(select(AuditLog)).scalars().all()
    )


def test_confirm_twice_rejected(session, monkeypatch):
    monkeypatch.setattr(
        "src.services.system.runtime_config.apply_runtime_settings_refresh",
        lambda *a, **kw: {},
    )
    action_id = _pending(session)
    svc, _ = _svc(session, [])
    svc.confirm_action(action_id=action_id, admin_user_id=9)
    with pytest.raises(ServiceException):
        svc.confirm_action(action_id=action_id, admin_user_id=9)


def test_confirm_non_whitelisted_key_rejected(session):
    """守卫: 即便数据层被塞进非法 key, confirm 也拒绝执行。"""
    action_id = _pending(session, key="binance.mainnet.api_secret", value="hack")
    svc, _ = _svc(session, [])
    with pytest.raises(ServiceException):
        svc.confirm_action(action_id=action_id, admin_user_id=9)
    # 配置未写入
    from src.models.system_setting import SystemSetting

    assert session.execute(select(SystemSetting)).scalars().all() == []
