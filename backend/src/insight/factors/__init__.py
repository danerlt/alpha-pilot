"""Factor layer per spec §5.2.

Indicators are raw (EMA/RSI/MACD/ATR/...); factors are semantic signals
normalized to [-1, 1] or [0, 1] that downstream decision logic consumes.
Separating the two lets Program Trader rules and LLM prompts speak the
same "factor language" and lets attribution decompose PnL by factor.
"""
