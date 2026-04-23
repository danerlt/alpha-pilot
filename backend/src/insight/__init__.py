"""Factor & Insight Plane per spec §5.

Indicators → Factors → Regime classification → Experience retrieval →
Attribution / Strategy scoring / Ops AI (V0.2+).

All modules here consume market data from `candles` and produce structured
signals that Strategy Plane consumes. Nothing here imports Strategy or
Execution code directly.
"""
