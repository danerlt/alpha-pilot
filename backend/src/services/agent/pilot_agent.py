"""PilotAgentService — Pilot AI 对话 (handoff 3.4)。

工具白名单只读为主; 唯一写口 propose_config_change 只落 pending 行,
人工 confirm 前不生效 —— Agent 无权直改硬风控。

工具协议 (prompt-based, 兼容任意 OpenAI 协议端点与 Mock):
  模型每轮只能输出一个 JSON:
    {"tool": "<name>", "args": {...}}   → 调工具, 结果回填继续
    {"final": "<回答文本>"}             → 结束
  解析失败时整段文本视为 final (兜底不空转)。工具循环上限 MAX_TOOL_ROUNDS。

SSE 事件流 (LLM 支持 complete_stream 时真流式: 纯文本回答边收边发 delta;
工具调用 JSON 需完整解析故缓冲; Mock/不支持流式的客户端回退切块伪流式):
  {"event": "tool_call", "data": {"name", "status": "start"|"done", "result"?}}
  {"event": "delta",     "data": {"text": ...}}
  {"event": "done",      "data": {"invocation_id", "pending_action_id"?}}
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Iterator

from sqlalchemy.orm import Session

from src.common.exception.errors import ServiceException
from src.core.exchange.adapter import ExchangeAdapter
from src.core.llm.client import LLMClient, LLMTimeout
from src.cruds.agent_pending_action_crud import agent_pending_action_crud
from src.cruds.decision_crud import ai_decision_crud
from src.cruds.position_crud import position_crud
from src.models.agent_invocation import AgentInvocation
from src.models.audit_log import AuditLog
from src.services.insight.experience.retriever import ExperienceRetriever
from src.services.risk.risk_state import RiskStateService

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4
_DELTA_CHUNK = 64

# 可确认配置白名单 = runtime_config 四个风控键; propose 与 confirm 双重校验
CONFIRMABLE_CONFIG_KEYS = {
    "risk.max_position_size_pct",
    "risk.max_daily_loss_pct",
    "risk.max_consecutive_losses",
    "risk.max_single_risk_pct",
}

_SYSTEM_PROMPT = """你是 AlphaPilot 交易系统的驾驶舱助手 Pilot AI。用中文回答。

你只能通过工具获取系统数据。每轮回复二选一：
1. 需要调工具时：只输出一个 JSON 对象（不要 markdown 代码块）：{"tool": "<工具名>", "args": {<参数>}}
2. 给用户最终回答时：**直接输出回答文本**（不要 JSON、不要代码块包裹）

可用工具:
- get_positions {} — 当前开仓持仓列表
- get_risk_state {} — 风控状态 (OK/WARN/HALTED, 日亏, 仓位占比, regime)
- get_decisions {"limit": 5} — 最近 AI 决策
- get_decision {"decision_id": 123} — 单条决策详情摘要
- get_market_ticker {"symbol": "BTCUSDT"} — 24h 行情
- get_experiences {"symbol": "BTCUSDT"} — 历史交易经验
- propose_config_change {"key": "...", "value": ..., "reason": "..."} — 提议修改风控配置。
  仅限键: risk.max_position_size_pct / risk.max_daily_loss_pct /
  risk.max_consecutive_losses / risk.max_single_risk_pct。
  该工具只生成待确认动作, 管理员确认后才生效; 你没有任何直接修改配置的权限。

安全规则: 不执行任何交易操作; 涉及配置修改一律走 propose_config_change 并在回答中说明"需管理员确认"。"""


class PilotAgentService:
    def __init__(self, session: Session, llm: LLMClient, adapter: ExchangeAdapter):
        self._session = session
        self._llm = llm
        self._adapter = adapter

    # ── 工具实现 (只读为主) ──────────────────────────────────────────────

    def _tool_get_positions(self, args: dict, ctx: dict) -> Any:
        rows = position_crud.find_open(
            self._session, trading_mode=ctx["trading_mode"], account_id=ctx["account_id"],
        )
        return [
            {
                "id": p.id, "symbol": p.symbol, "quantity": float(p.quantity),
                "entry_price": float(p.entry_price),
                "current_price": float(p.current_price or 0),
                "stop_loss": float(p.stop_loss),
                "take_profit": float(p.take_profit) if p.take_profit else None,
                "unrealized_pnl": float(p.unrealized_pnl or 0),
            }
            for p in rows
        ]

    def _tool_get_risk_state(self, args: dict, ctx: dict) -> Any:
        return RiskStateService(self._session).compute(
            trading_mode=ctx["trading_mode"], account_id=ctx["account_id"],
        )

    def _tool_get_decisions(self, args: dict, ctx: dict) -> Any:
        from sqlalchemy import select

        from src.models.decision import AIDecision

        limit = min(int(args.get("limit", 5)), 20)
        rows = self._session.execute(
            select(AIDecision)
            .where(AIDecision.trading_mode == ctx["trading_mode"])
            .order_by(AIDecision.decided_at.desc()).limit(limit)
        ).scalars().all()
        return [
            {
                "id": d.id, "symbol": d.symbol, "action": d.action,
                "confidence": float(d.confidence) if d.confidence else None,
                "is_fallback": d.is_fallback,
                "decided_at": d.decided_at.isoformat(),
            }
            for d in rows
        ]

    def _tool_get_decision(self, args: dict, ctx: dict) -> Any:
        d = ai_decision_crud.get_or_none(self._session, int(args["decision_id"]))
        if d is None or d.trading_mode != ctx["trading_mode"]:
            return {"error": "decision not found"}
        return {
            "id": d.id, "symbol": d.symbol, "action": d.action,
            "confidence": float(d.confidence) if d.confidence else None,
            "reasoning": d.reasoning, "risk_note": d.risk_note,
            "entry_price": float(d.entry_price) if d.entry_price else None,
            "stop_loss": float(d.stop_loss) if d.stop_loss else None,
            "take_profit": float(d.take_profit) if d.take_profit else None,
            "is_fallback": d.is_fallback,
        }

    def _tool_get_market_ticker(self, args: dict, ctx: dict) -> Any:
        from src.services.execution.market_query import MarketQueryService

        return MarketQueryService(self._session, self._adapter).get_ticker(
            symbol=str(args["symbol"]).upper(),
        )

    def _tool_get_experiences(self, args: dict, ctx: dict) -> Any:
        rows = ExperienceRetriever(self._session).top_k(
            account_id=ctx["account_id"], symbol=str(args["symbol"]).upper(),
        )
        return [
            {
                "symbol": e.symbol, "regime_at_open": e.regime_at_open,
                "strategy_mode": e.strategy_mode, "pnl_pct": e.pnl_pct,
                "exit_reason": e.exit_reason,
            }
            for e in rows
        ]

    def _tool_propose_config_change(self, args: dict, ctx: dict) -> Any:
        key = str(args.get("key", ""))
        if key not in CONFIRMABLE_CONFIG_KEYS:
            return {"error": f"key 不在可确认白名单: {sorted(CONFIRMABLE_CONFIG_KEYS)}"}
        if "value" not in args:
            return {"error": "缺少 value"}
        row = agent_pending_action_crud.add(
            self._session,
            action_type="config_change",
            payload_json={
                "key": key, "value": args["value"],
                "reason": str(args.get("reason", "")),
            },
            status="PENDING",
            proposed_at=datetime.now(tz=timezone.utc),
        )
        ctx["pending_action_id"] = row.id
        return {
            "action_id": row.id, "status": "pending_confirmation",
            "note": "已生成待确认动作, 管理员确认后才生效",
        }

    @property
    def _tools(self) -> dict:
        return {
            "get_positions": self._tool_get_positions,
            "get_risk_state": self._tool_get_risk_state,
            "get_decisions": self._tool_get_decisions,
            "get_decision": self._tool_get_decision,
            "get_market_ticker": self._tool_get_market_ticker,
            "get_experiences": self._tool_get_experiences,
            "propose_config_change": self._tool_propose_config_change,
        }

    # ── chat 主循环 ─────────────────────────────────────────────────────

    def chat(
        self,
        *,
        message: str,
        user_id: int,
        trading_mode: str,
        account_id: int = 1,
        timeout_s: int = 30,
    ) -> Iterator[dict]:
        """工具循环 → 产出 SSE 事件 dict; 结束前落 agent_invocations 行 + commit。"""
        started = time.monotonic()
        ctx: dict[str, Any] = {
            "trading_mode": trading_mode, "account_id": account_id,
            "pending_action_id": None,
        }
        transcript = f"用户: {message}"
        tools_used: list[str] = []
        answer = ""
        outcome = "success"
        error: str | None = None

        streamed = False
        try:
            for _ in range(MAX_TOOL_ROUNDS + 1):
                stream_fn = getattr(self._llm, "complete_stream", None)
                if stream_fn is not None:
                    raw_text, streamed_pieces = "", []
                    emitting = False
                    for piece in stream_fn(
                        system=_SYSTEM_PROMPT, user=transcript,
                        max_tokens=1024, timeout_s=timeout_s,
                    ):
                        if emitting:
                            answer += piece
                            yield {"event": "delta", "data": {"text": piece}}
                            continue
                        streamed_pieces.append(piece)
                        joined = "".join(streamed_pieces)
                        stripped = joined.lstrip()
                        if not stripped:
                            continue
                        if stripped[0] == "{" or stripped.startswith("`"):
                            continue  # 疑似工具 JSON / 代码块 → 缓冲到完整再解析
                        # 纯文本回答 → 切换真流式直发
                        emitting = True
                        answer = joined
                        yield {"event": "delta", "data": {"text": joined}}
                    if emitting:
                        streamed = True
                        break
                    raw_text = "".join(streamed_pieces)
                else:
                    raw_text = self._llm.complete(
                        system=_SYSTEM_PROMPT, user=transcript,
                        max_tokens=1024, timeout_s=timeout_s,
                    ).raw_text
                parsed = self._parse(raw_text)
                if "tool" in parsed:
                    name = parsed["tool"]
                    args = parsed.get("args") or {}
                    yield {"event": "tool_call", "data": {"name": name, "status": "start"}}
                    tool_fn = self._tools.get(name)
                    if tool_fn is None:
                        tool_result: Any = {"error": f"unknown tool: {name}"}
                    else:
                        try:
                            tool_result = tool_fn(args, ctx)
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("agent tool %s failed", name, exc_info=True)
                            tool_result = {"error": str(exc)[:200]}
                    tools_used.append(name)
                    yield {"event": "tool_call", "data": {"name": name, "status": "done"}}
                    transcript += (
                        f"\n[工具 {name} 返回]: {json.dumps(tool_result, ensure_ascii=False, default=str)[:2000]}"
                        "\n请继续 (输出 tool 或 final JSON):"
                    )
                    continue
                answer = parsed["final"]
                break
            else:
                answer = "抱歉, 本轮推理超出工具调用上限, 请换个问法。"
        except LLMTimeout:
            outcome = "timeout"
            error = "llm_timeout"
            answer = "抱歉, AI 服务响应超时, 请稍后重试。"

        if not streamed:
            for i in range(0, len(answer), _DELTA_CHUNK):
                yield {"event": "delta", "data": {"text": answer[i:i + _DELTA_CHUNK]}}

        invocation = AgentInvocation(
            account_id=account_id,
            agent_type="pilot_chat",
            input_hash=hashlib.sha256(message.encode()).hexdigest(),
            llm_provider=getattr(self._llm, "provider", None),
            input_json={"message": message, "user_id": user_id},
            output_json={
                "answer": answer, "tools": tools_used,
                "pending_action_id": ctx["pending_action_id"],
            },
            latency_ms=int((time.monotonic() - started) * 1000),
            outcome=outcome,
            error=error,
            occurred_at=datetime.now(tz=timezone.utc),
        )
        self._session.add(invocation)
        self._session.commit()

        done_data: dict[str, Any] = {"invocation_id": invocation.id}
        if ctx["pending_action_id"] is not None:
            done_data["pending_action_id"] = ctx["pending_action_id"]
        yield {"event": "done", "data": done_data}

    @staticmethod
    def _parse(raw: str) -> dict:
        """模型输出 → {"tool", "args"} 或 {"final"}; 解析失败整段视为 final。"""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return {"final": raw.strip()}
        if isinstance(obj, dict) and "tool" in obj:
            return {"tool": str(obj["tool"]), "args": obj.get("args") or {}}
        if isinstance(obj, dict) and "final" in obj:
            return {"final": str(obj["final"])}
        return {"final": raw.strip()}

    # ── 历史 / 确认 ─────────────────────────────────────────────────────

    def history(self, *, limit: int = 20, account_id: int = 1) -> list[dict]:
        from sqlalchemy import select

        rows = self._session.execute(
            select(AgentInvocation)
            .where(
                AgentInvocation.account_id == account_id,
                AgentInvocation.agent_type == "pilot_chat",
            )
            .order_by(AgentInvocation.id.desc()).limit(min(limit, 100))
        ).scalars().all()
        return [
            {
                "invocation_id": r.id,
                "message": (r.input_json or {}).get("message"),
                "answer": (r.output_json or {}).get("answer"),
                "tools": (r.output_json or {}).get("tools", []),
                "pending_action_id": (r.output_json or {}).get("pending_action_id"),
                "occurred_at": r.occurred_at.isoformat(),
            }
            for r in rows
        ]

    def confirm_action(self, *, action_id: int, admin_user_id: int) -> dict:
        """人工确认 pending action → 应用 runtime config + 审计。本方法 commit。"""
        from src.configs.app_configs import get_settings
        from src.services.system.runtime_config import (
            apply_runtime_settings_refresh,
            build_fernet,
            upsert_system_setting,
        )

        action = agent_pending_action_crud.get(self._session, action_id)
        if action.status != "PENDING":
            raise ServiceException(f"action {action_id} 状态为 {action.status}, 不可确认")
        payload = action.payload_json or {}
        key = str(payload.get("key", ""))
        # confirm 时再次校验白名单 (防 Agent/数据层绕过)
        if key not in CONFIRMABLE_CONFIG_KEYS:
            raise ServiceException(f"action {action_id} 的 key 不在可确认白名单: {key}")

        settings = get_settings()
        fernet = build_fernet(settings.APP_CONFIG_MASTER_KEY)
        upsert_system_setting(
            self._session, key=key, value=payload.get("value"), fernet=fernet,
            description=f"pilot_agent action {action_id}: {payload.get('reason', '')}"[:200],
        )
        agent_pending_action_crud.mark_confirmed(
            self._session, action_id, confirmed_by=admin_user_id,
        )
        self._session.add(AuditLog(
            account_id=1, user_id=admin_user_id,
            action="agent_action_confirm", resource_type="agent_pending_action",
            resource_id=str(action_id), after_json=payload,
        ))
        self._session.commit()
        mode = settings.TRADING_MODE
        try:
            apply_runtime_settings_refresh(
                self._session,
                master_key=settings.APP_CONFIG_MASTER_KEY,
                default_trading_mode=mode,
            )
        except Exception:  # noqa: BLE001
            logger.warning("runtime settings refresh failed after confirm (non-fatal)", exc_info=True)
        # ADR-0001 P2: 广播变更，其它进程订到即重载
        from src.services.system.config_pubsub import publish_config_changed

        publish_config_changed()
        return {"action_id": action_id, "status": "CONFIRMED", "key": key, "value": payload.get("value")}
