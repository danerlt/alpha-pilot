"""市场状态识别服务 — 基于技术指标判断 trending_up/trending_down/ranging/chaotic。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.services.insight.indicators_calculator import IndicatorResult, get_latest_indicators
from src.shared.config import get_settings
from src.shared.enums import RegimeType
from src.models.regime import RegimeSnapshot

logger = logging.getLogger(__name__)

# 判定阈值（可后续迁移到配置中心）
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
ATR_VOLATILITY_HIGH = 0.03   # 波动率 > 3% 视为高波动
ADX_TREND_THRESHOLD = 25.0   # ADX > 25 视为有趋势（此处用 EMA 斜率替代）


def classify_regime(ind: IndicatorResult) -> tuple[RegimeType, float, dict]:
    """
    根据指标判断市场状态，返回 (regime, confidence, features)。

    规则（优先级从高到低）：
    1. CHAOTIC: ATR 极高 / 波动率异常 → 停止策略
    2. TRENDING_UP: EMA20 > EMA50 > EMA200 && RSI > 50 && MACD > Signal
    3. TRENDING_DOWN: EMA20 < EMA50 < EMA200 && RSI < 50 && MACD < Signal
    4. RANGING: 其余情况
    """
    features: dict = {}

    # 波动率检测
    vol = ind.volatility or 0.0
    features["volatility"] = vol
    if vol > ATR_VOLATILITY_HIGH:
        return RegimeType.CHAOTIC, round(min(0.5 + vol * 10, 0.95), 4), features

    # EMA 排列
    ema20 = ind.ema20
    ema50 = ind.ema50
    ema200 = ind.ema200
    rsi = ind.rsi or 50.0
    macd = ind.macd or 0.0
    macd_sig = ind.macd_signal or 0.0

    features.update(
        ema20=ema20,
        ema50=ema50,
        ema200=ema200,
        rsi=rsi,
        macd=macd,
        macd_signal=macd_sig,
    )

    score_up = 0
    score_down = 0
    total = 0

    # EMA 排列
    if ema20 is not None and ema50 is not None:
        total += 1
        if ema20 > ema50:
            score_up += 1
        else:
            score_down += 1

    if ema50 is not None and ema200 is not None:
        total += 1
        if ema50 > ema200:
            score_up += 1
        else:
            score_down += 1

    # RSI
    total += 1
    if rsi > 55:
        score_up += 1
    elif rsi < 45:
        score_down += 1

    # MACD vs Signal
    total += 1
    if macd > macd_sig:
        score_up += 1
    else:
        score_down += 1

    if total == 0:
        return RegimeType.RANGING, 0.5, features

    confidence_up = score_up / total
    confidence_down = score_down / total

    if confidence_up >= 0.75:
        return RegimeType.TRENDING_UP, round(confidence_up, 4), features
    if confidence_down >= 0.75:
        return RegimeType.TRENDING_DOWN, round(confidence_down, 4), features

    return RegimeType.RANGING, round(1.0 - abs(confidence_up - confidence_down), 4), features


def classify_and_store(db: Session, symbol: str, timeframe: str) -> RegimeSnapshot | None:
    """读取最新指标快照 → 识别市场状态 → 写入 regime_snapshots。"""
    settings = get_settings()

    ind_snap = get_latest_indicators(db, symbol, timeframe)
    if ind_snap is None:
        logger.warning("No indicator snapshot found for %s %s", symbol, timeframe)
        return None

    from src.services.insight.indicators_calculator import IndicatorResult
    ind = IndicatorResult(
        ema20=float(ind_snap.ema20) if ind_snap.ema20 else None,
        ema50=float(ind_snap.ema50) if ind_snap.ema50 else None,
        ema200=float(ind_snap.ema200) if ind_snap.ema200 else None,
        rsi=float(ind_snap.rsi) if ind_snap.rsi else None,
        macd=float(ind_snap.macd) if ind_snap.macd else None,
        macd_signal=float(ind_snap.macd_signal) if ind_snap.macd_signal else None,
        macd_hist=float(ind_snap.macd_hist) if ind_snap.macd_hist else None,
        atr=float(ind_snap.atr) if ind_snap.atr else None,
        volatility=float(ind_snap.volatility) if ind_snap.volatility else None,
    )

    regime, confidence, features = classify_regime(ind)

    snap = RegimeSnapshot(
        trading_mode=settings.TRADING_MODE.value,
        symbol=symbol,
        timeframe=timeframe,
        snapshot_at=datetime.now(tz=timezone.utc),
        regime=regime.value,
        confidence=confidence,
        features=features,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    logger.info("Regime classified for %s %s: %s (confidence=%.2f)", symbol, timeframe, regime.value, confidence)
    return snap


def get_latest_regime(db: Session, symbol: str, timeframe: str) -> RegimeSnapshot | None:
    settings = get_settings()
    return (
        db.query(RegimeSnapshot)
        .filter(
            RegimeSnapshot.trading_mode == settings.TRADING_MODE.value,
            RegimeSnapshot.symbol == symbol,
            RegimeSnapshot.timeframe == timeframe,
        )
        .order_by(RegimeSnapshot.snapshot_at.desc())
        .first()
    )
