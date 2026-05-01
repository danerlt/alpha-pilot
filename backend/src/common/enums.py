from enum import Enum


class TradingMode(str, Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class Action(str, Enum):
    OPEN_LONG = "OPEN_LONG"
    CLOSE_LONG = "CLOSE_LONG"
    HOLD = "HOLD"
    # V0.1 不支持做空（OPEN_SHORT / CLOSE_SHORT 在 V0.3+ 支持）


class EntryType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class StrategyMode(str, Enum):
    TREND_FOLLOWING = "trend_following"
    BREAKOUT = "breakout"
    OBSERVATION = "observation"


class RegimeType(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    CHAOTIC = "chaotic"


class GuardResult(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"
    DEGRADE = "DEGRADE"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class TradeExitReason(str, Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    AI_CLOSE = "ai_close"
    MANUAL_CLOSE = "manual_close"
    CIRCUIT_BREAKER = "circuit_breaker"
    PARTIAL = "partial"
