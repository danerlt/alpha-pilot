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
        # start 的记录放在最前: 即使 session factory 失败也要记住当前阶段
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
