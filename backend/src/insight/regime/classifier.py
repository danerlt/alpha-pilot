"""RegimeClassifier — factor-based market state classification (spec §5.3).

Rules (defaults; override via constructor `thresholds`):

  chaotic        ← volatility_regime >= 0.80
                 OR breakout_validity <= -0.50
  trending_up    ← trend_strength > 0.60  AND volatility_regime <  0.80
  trending_down  ← trend_strength < -0.60 AND volatility_regime <  0.80
  ranging        ← |trend_strength| < 0.30 AND volatility_regime < 0.40
  (else)         ← ranging as fallback  (mid-band trend with moderate vol)

Confidence ∈ [0, 1]:
  trending/ranging:   distance from the qualifying threshold, scaled to [0, 1]
  chaotic:            how far above the volatility_regime threshold
  fallback ranging:   0.3  (low but non-zero to flag "uncertain")

Missing factors are treated as 0 — this keeps the system from freezing on
partial data; callers upstream should have already checked indicator/factor
validity before calling.

并发安全 (Plan 5 codereview I6):
  classify_and_store 当前用 "delete-then-insert" 模拟 UPSERT, 与
  FactorComputer 同样要求 V0.1 单 worker 串行运行. V0.2+ 上多 worker 后
  需要切到 Postgres ON CONFLICT DO UPDATE; SQLite 单测路径不变。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.shared.models.regime import RegimeSnapshot


RegimeType = Literal["trending_up", "trending_down", "ranging", "chaotic"]


@dataclass
class RegimeResult:
    regime: RegimeType
    confidence: float  # [0, 1]


# V0.1 defaults — calibration point; learning controller can overwrite.
DEFAULT_THRESHOLDS = {
    "chaotic_vol_threshold": 0.80,
    "chaotic_breakout_floor": -0.50,
    "trending_strength": 0.60,
    "ranging_strength_band": 0.30,
    "ranging_vol_ceiling": 0.40,
}


class RegimeClassifier:
    def __init__(self, thresholds: dict | None = None):
        # Shallow-merge user overrides onto defaults.
        self._t = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            self._t.update(thresholds)

    def classify(self, factors: dict[str, float]) -> RegimeResult:
        ts = factors.get("trend_strength", 0.0)
        vr = factors.get("volatility_regime", 0.5)
        bv = factors.get("breakout_validity", 0.0)

        # 1. Chaotic — first so it overrides any other classification.
        if vr >= self._t["chaotic_vol_threshold"] or bv <= self._t["chaotic_breakout_floor"]:
            # Confidence: scale how far we are past whichever trigger fired.
            from_vol = max(0.0, (vr - self._t["chaotic_vol_threshold"]) / max(1e-9, 1.0 - self._t["chaotic_vol_threshold"]))
            from_bv = max(0.0, (self._t["chaotic_breakout_floor"] - bv) / max(1e-9, 1.0 + self._t["chaotic_breakout_floor"]))
            confidence = min(1.0, max(from_vol, from_bv, 0.5))  # floor 0.5
            return RegimeResult(regime="chaotic", confidence=confidence)

        # 2. Trending up.
        if ts > self._t["trending_strength"] and vr < self._t["chaotic_vol_threshold"]:
            confidence = min(1.0, (ts - self._t["trending_strength"]) / max(1e-9, 1.0 - self._t["trending_strength"]))
            confidence = max(confidence, 0.3)
            return RegimeResult(regime="trending_up", confidence=confidence)

        # 3. Trending down.
        if ts < -self._t["trending_strength"] and vr < self._t["chaotic_vol_threshold"]:
            confidence = min(1.0, (-ts - self._t["trending_strength"]) / max(1e-9, 1.0 - self._t["trending_strength"]))
            confidence = max(confidence, 0.3)
            return RegimeResult(regime="trending_down", confidence=confidence)

        # 4. Ranging: weak trend + low volatility.
        if abs(ts) < self._t["ranging_strength_band"] and vr < self._t["ranging_vol_ceiling"]:
            # Confidence: the closer to 0 the trend and the lower the vol, the more confident.
            band = self._t["ranging_strength_band"]
            vol_ceil = self._t["ranging_vol_ceiling"]
            trend_conf = 1.0 - abs(ts) / max(1e-9, band)  # 1 at 0, 0 at band
            vol_conf = 1.0 - vr / max(1e-9, vol_ceil)     # 1 at 0, 0 at vol_ceil
            confidence = min(1.0, max(0.3, (trend_conf + vol_conf) / 2.0))
            return RegimeResult(regime="ranging", confidence=confidence)

        # 5. Fallback: neither clearly trending nor cleanly ranging — call it ranging with low confidence.
        return RegimeResult(regime="ranging", confidence=0.3)

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
        """Classify + UPSERT to regime_snapshots (delete-and-insert on the unique key)."""
        result = self.classify(factors)

        session.execute(
            delete(RegimeSnapshot).where(
                RegimeSnapshot.account_id == account_id,
                RegimeSnapshot.trading_mode == trading_mode,
                RegimeSnapshot.symbol == symbol,
                RegimeSnapshot.timeframe == timeframe,
                RegimeSnapshot.snapshot_at == open_time,
            )
        )
        snap = RegimeSnapshot(
            account_id=account_id,
            trading_mode=trading_mode,
            symbol=symbol,
            timeframe=timeframe,
            snapshot_at=open_time,
            regime=result.regime,
            confidence=result.confidence,
            # `factor_snapshot_id` column not yet on the regime_snapshots
            # table (spec §6.6 lists it; Plan 1 migrations omitted it).
            # Stash in `features` JSON until Plan 5 adds the column.
            features={"factor_snapshot_id": factor_snapshot_id, "factors": factors},
        )
        session.add(snap)
        session.flush()
        return result
