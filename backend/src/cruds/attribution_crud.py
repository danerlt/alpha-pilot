"""CRUD for src.models.attribution."""
from __future__ import annotations

from src.models.attribution import StrategyScore, TradeAttribution
from src.cruds.base_crud import BaseCrud


class StrategyScoreCrud(BaseCrud[StrategyScore]):
    model = StrategyScore

strategy_score_crud = StrategyScoreCrud()

class TradeAttributionCrud(BaseCrud[TradeAttribution]):
    model = TradeAttribution

trade_attribution_crud = TradeAttributionCrud()
