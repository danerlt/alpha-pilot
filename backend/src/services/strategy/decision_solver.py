"""DecisionSolver — call LLM, parse JSON, validate, persist ai_decisions.

All failure paths funnel to the canonical fallback HOLD:
  - LLMTimeout
  - JSON parse failure
  - action not in whitelist (no OPEN_SHORT etc.)
  - missing stop_loss when action != HOLD
  - position_size_pct > MAX_POSITION_SIZE_PCT (hard-cap per spec §1.4)
  - Pydantic ValidationError on DecisionProposal

Any fallback still writes an ai_decisions row (is_fallback=True) so the
audit trail captures the attempted decision + the LLM raw output.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.shared.constants import MAX_POSITION_SIZE_PCT_HARD_CAP
from src.models.decision import AIDecision
from src.core.llm.client import LLMClient, LLMResult, LLMTimeout
from src.services.strategy.prompt_composer import PromptBundle
from src.services.strategy.proposal import DecisionProposal

logger = logging.getLogger(__name__)

# Strip common code-fence wrappers before json.loads.
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text).strip()


def _reject_non_finite(value):
    """json.loads 的 parse_constant hook: 显式拒 NaN / Infinity / -Infinity.

    Python json 默认接受这三个非标准扩展, 让恶意/越狱 LLM 可输出
    {"stop_loss": NaN} 后在下游绕过所有数值比较 (NaN 与任何值比较都是
    False). post-Plan5 安全审计 C6.
    """
    raise ValueError(f"non-finite JSON constant rejected: {value!r}")


def _parse_llm_json(raw: str) -> dict:
    """Extract the first JSON object from the raw LLM output."""
    cleaned = _strip_code_fences(raw)
    # If LLM added prose, isolate the first {...} balanced block.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object found in LLM output: {raw[:120]!r}")
    return json.loads(cleaned[start:end + 1], parse_constant=_reject_non_finite)


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
        factor_snapshot_id: int | None,
    ) -> tuple[DecisionProposal, int]:
        """Returns (proposal, ai_decisions_id). Never raises on normal
        error paths — fall back to HOLD and record the reason."""
        raw_output = ""
        llm_result: LLMResult | None = None
        fallback_reason: str | None = None
        proposal: DecisionProposal

        try:
            llm_result = self._llm.complete(
                system=prompt_bundle.system,
                user=prompt_bundle.user,
            )
            raw_output = llm_result.raw_text

            data = _parse_llm_json(raw_output)
            # Action gate — DecisionProposal's Literal would reject anyway,
            # but check here first so we can attribute the failure cleanly.
            action = data.get("action")
            if action not in {"OPEN_LONG", "CLOSE_LONG", "HOLD"}:
                raise ValueError(f"invalid action: {action!r}")

            # Non-HOLD must supply stop_loss.
            if action != "HOLD" and data.get("stop_loss") is None:
                raise ValueError("missing stop_loss on non-HOLD action")

            # Hard-cap position size regardless of LLM claim.
            size = data.get("position_size_pct")
            if size is not None and size > MAX_POSITION_SIZE_PCT_HARD_CAP:
                raise ValueError(
                    f"position_size_pct {size} exceeds hard cap {MAX_POSITION_SIZE_PCT_HARD_CAP}"
                )

            proposal = DecisionProposal(
                account_id=account_id,
                symbol=symbol,
                timeframe=timeframe,
                action=action,
                confidence=float(data.get("confidence", 0.0)),
                entry_type=data.get("entry_type"),
                entry_price=data.get("entry_price"),
                stop_loss=data.get("stop_loss"),
                take_profit=data.get("take_profit"),
                position_size_pct=size,
                strategy_mode=data.get("strategy_mode", "ai_trend"),
                reasoning=data.get("reasoning", []) or [],
                risk_note=data.get("risk_note"),
                source="ai_trader",
                prompt_template_id=prompt_bundle.template_id,
                llm_model_id=llm_result.model if llm_result else None,
                factor_snapshot_id=factor_snapshot_id,
                is_fallback=False,
            )

        except LLMTimeout as e:
            fallback_reason = f"llm_timeout:{e}"
        except (ValueError, ValidationError, KeyError) as e:
            fallback_reason = f"parse_or_validation:{e}"
        except Exception as e:  # noqa: BLE001 — last-resort safety net
            logger.exception("unexpected DecisionSolver error; falling back to HOLD")
            fallback_reason = f"unexpected:{e}"

        if fallback_reason is not None:
            proposal = DecisionProposal.fallback_hold(
                account_id=account_id,
                symbol=symbol,
                timeframe=timeframe,
                reason=fallback_reason,
                factor_snapshot_id=factor_snapshot_id,
            )
            proposal.prompt_template_id = prompt_bundle.template_id
            if llm_result is not None:
                proposal.llm_model_id = llm_result.model

        # Persist ai_decisions row regardless of fallback — audit trail.
        decision_row = AIDecision(
            account_id=account_id,
            trading_mode=trading_mode,
            symbol=symbol,
            timeframe=timeframe,
            decided_at=datetime.now(tz=timezone.utc),
            action=proposal.action,
            confidence=proposal.confidence,
            entry_type=proposal.entry_type,
            entry_price=proposal.entry_price,
            stop_loss=proposal.stop_loss,
            take_profit=proposal.take_profit,
            position_size_pct=proposal.position_size_pct,
            strategy_mode=proposal.strategy_mode,
            reasoning=proposal.reasoning,
            risk_note=proposal.risk_note,
            prompt_input={"context_hash": prompt_bundle.context_hash},
            raw_output=raw_output,
            is_fallback=proposal.is_fallback,
            proposal_draft_id=prompt_bundle.proposal_draft_id,
            llm_provider=llm_result.provider if llm_result else None,
            llm_model=llm_result.model if llm_result else None,
            tokens_used=llm_result.tokens_used if llm_result else None,
            latency_ms=llm_result.latency_ms if llm_result else None,
            source="ai_trader",
            factor_snapshot_id=factor_snapshot_id,
        )
        self._session.add(decision_row)
        self._session.flush()

        return proposal, decision_row.id
