"""Prompt 模板构建 — 将市场快照格式化为 LLM 输入。"""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """You are AlphaPilot, an AI trading assistant for Binance spot markets.
You make structured trading decisions based on technical indicators and market regime.

Rules:
- V0.1 only supports spot LONG positions (no shorting).
- Actions: OPEN_LONG, CLOSE_LONG, HOLD.
- You MUST return valid JSON matching the schema exactly.
- stop_loss is REQUIRED for OPEN_LONG (must be below entry_price).
- take_profit is recommended but optional.
- position_size_pct must be between 0.01 and 0.20.
- Be conservative: when in doubt, output HOLD.

Output ONLY the JSON object, no markdown, no explanation."""

DECISION_SCHEMA = """{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "action": "OPEN_LONG | CLOSE_LONG | HOLD",
  "confidence": 0.0-1.0,
  "entry_type": "MARKET | LIMIT",
  "entry_price": <number or null>,
  "stop_loss": <number, REQUIRED for OPEN_LONG>,
  "take_profit": <number or null>,
  "position_size_pct": 0.01-0.20,
  "strategy_mode": "trend_following | breakout | observation",
  "reasoning": ["reason1", "reason2"],
  "risk_note": "brief risk description"
}"""


def build_prompt_input(
    symbol: str,
    timeframe: str,
    current_price: float,
    indicators: dict[str, Any],
    regime: dict[str, Any],
    account: dict[str, Any],
    open_position: dict[str, Any] | None,
    recent_experience: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """构建完整 prompt 输入字典（同时用于审计存储）。"""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "current_price": current_price,
        "indicators": indicators,
        "regime": regime,
        "account": account,
        "open_position": open_position,
        "recent_experience": recent_experience or [],
    }


def format_user_message(prompt_input: dict[str, Any]) -> str:
    """将 prompt_input 转换为用户消息文本。"""
    ind = prompt_input.get("indicators", {})
    regime = prompt_input.get("regime", {})
    account = prompt_input.get("account", {})
    pos = prompt_input.get("open_position")
    exp = prompt_input.get("recent_experience", [])

    lines = [
        f"Symbol: {prompt_input['symbol']} | Timeframe: {prompt_input['timeframe']}",
        f"Current Price: {prompt_input['current_price']:.4f} USDT",
        "",
        "=== Technical Indicators ===",
        f"EMA20: {ind.get('ema20', 'N/A')} | EMA50: {ind.get('ema50', 'N/A')} | EMA200: {ind.get('ema200', 'N/A')}",
        f"RSI(14): {ind.get('rsi', 'N/A')} | ATR(14): {ind.get('atr', 'N/A')}",
        f"MACD: {ind.get('macd', 'N/A')} | Signal: {ind.get('macd_signal', 'N/A')} | Hist: {ind.get('macd_hist', 'N/A')}",
        f"BB Upper: {ind.get('bb_upper', 'N/A')} | BB Mid: {ind.get('bb_middle', 'N/A')} | BB Lower: {ind.get('bb_lower', 'N/A')}",
        f"Volume MA: {ind.get('volume_ma', 'N/A')} | Volatility(20): {ind.get('volatility', 'N/A')}",
        "",
        "=== Market Regime ===",
        f"Regime: {regime.get('regime', 'N/A')} | Confidence: {regime.get('confidence', 'N/A')}",
        "",
        "=== Account State ===",
        f"Available USDT: {account.get('available_usdt', 0):.2f} | Daily PnL: {account.get('daily_pnl', 0):.4f} ({account.get('daily_pnl_pct', 0)*100:.2f}%)",
    ]

    if pos:
        lines += [
            "",
            "=== Open Position ===",
            f"Symbol: {pos.get('symbol')} | Qty: {pos.get('quantity')} | Entry: {pos.get('entry_price')}",
            f"Stop Loss: {pos.get('stop_loss')} | Take Profit: {pos.get('take_profit')}",
            f"Unrealized PnL: {pos.get('unrealized_pnl', 0):.4f} USDT",
        ]
    else:
        lines.append("")
        lines.append("No open position.")

    if exp:
        lines += ["", "=== Recent Experience (last 3 trades) ==="]
        for e in exp[:3]:
            lines.append(
                f"  {e.get('symbol')} {e.get('exit_reason')} PnL={e.get('pnl_pct', 0)*100:.2f}% "
                f"regime={e.get('regime')} strategy={e.get('strategy_mode')}"
            )

    lines += [
        "",
        "=== Decision Schema ===",
        DECISION_SCHEMA,
        "",
        "Make your trading decision:",
    ]

    return "\n".join(lines)
