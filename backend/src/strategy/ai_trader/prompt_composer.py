"""PromptComposer — render prompt templates against a context, persist draft.

Loads the active prompt_templates row by `name`, fills `${var}` placeholders
with the structured context, hashes the (canonical) context for dedup /
replay, writes a proposal_drafts row, returns a PromptBundle.

V0.1 uses `string.Template` ($var substitution) to avoid a Jinja2 dependency.
V0.2+ can swap to Jinja once template logic gets richer.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from string import Template

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.models.prompt import PromptTemplate, ProposalDraft


@dataclass
class PromptContext:
    account_id: int
    symbol: str
    timeframe: str
    current_price: float
    indicators: dict[str, float | None]
    factors: dict[str, float]
    regime: str
    open_position: dict | None              # None = no open position
    account_snapshot: dict                  # {available_usdt, daily_pnl, daily_pnl_pct}
    recent_experience: list[dict]           # ExperienceSummary dumps

    def canonical_json(self) -> str:
        """Stable JSON form used for context_hash. Sorted keys, no whitespace."""
        return json.dumps(self._as_dict(), sort_keys=True, separators=(",", ":"), default=str)

    def _as_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "indicators": self.indicators,
            "factors": self.factors,
            "regime": self.regime,
            "open_position": self.open_position,
            "account_snapshot": self.account_snapshot,
            "recent_experience": self.recent_experience,
        }


@dataclass
class PromptBundle:
    proposal_draft_id: int
    template_id: int
    template_name: str
    template_version: int
    system: str
    user: str
    context_hash: str  # SHA-256 hex (64 chars)


class PromptTemplateNotFound(RuntimeError):
    pass


class PromptComposer:
    """Stateless helper bound to a Session. Safe to reuse per cycle."""

    def __init__(self, session: Session):
        self._session = session

    def compose(
        self,
        ctx: PromptContext,
        *,
        template_name: str = "ait_default",
    ) -> PromptBundle:
        """Render the active template with `template_name`; persist a
        proposal_drafts row; return the bundle."""
        template = self._session.execute(
            select(PromptTemplate)
            .where(PromptTemplate.name == template_name, PromptTemplate.active.is_(True))
            .order_by(PromptTemplate.version.desc())
        ).scalars().first()

        if template is None:
            raise PromptTemplateNotFound(
                f"no active prompt_templates row with name={template_name!r}"
            )

        canonical = ctx.canonical_json()
        context_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        variables = {
            "symbol": ctx.symbol,
            "timeframe": ctx.timeframe,
            "current_price": ctx.current_price,
            "regime": ctx.regime,
            "indicators_json": json.dumps(ctx.indicators, sort_keys=True, default=str),
            "factors_json": json.dumps(ctx.factors, sort_keys=True, default=str),
            "open_position_json": json.dumps(ctx.open_position, sort_keys=True, default=str),
            "account_snapshot_json": json.dumps(ctx.account_snapshot, sort_keys=True, default=str),
            "recent_experience_json": json.dumps(ctx.recent_experience, sort_keys=True, default=str),
        }

        system = Template(template.system_template).safe_substitute(variables)
        user = Template(template.user_template).safe_substitute(variables)

        draft = ProposalDraft(
            account_id=ctx.account_id,
            trading_mode="testnet",  # caller controls mode; pipeline will override if needed
            symbol=ctx.symbol,
            timeframe=ctx.timeframe,
            template_id=template.id,
            context_hash=context_hash,
            rendered_system=system,
            rendered_user=user,
        )
        self._session.add(draft)
        self._session.flush()

        return PromptBundle(
            proposal_draft_id=draft.id,
            template_id=template.id,
            template_name=template.name,
            template_version=template.version,
            system=system,
            user=user,
            context_hash=context_hash,
        )
