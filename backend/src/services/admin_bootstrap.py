from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.common.enums import UserRole, UserStatus
from src.configs.app_configs import AppConfig as Settings
from src.models.user import User
from src.services.auth import hash_password, verify_password

logger = logging.getLogger(__name__)


def _derive_username(settings: Settings) -> str:
    if settings.DEFAULT_ADMIN_USERNAME.strip():
        return settings.DEFAULT_ADMIN_USERNAME.strip()
    email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()
    return (email.split('@')[0] if '@' in email else email)[:50] or 'admin'


def ensure_default_admin(db: Session, settings: Settings) -> bool:
    email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()
    password = settings.DEFAULT_ADMIN_PASSWORD
    if not email or not password:
        return False

    username = _derive_username(settings)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
        )
        db.add(user)
        db.commit()
        logger.info("Bootstrapped default admin user: %s", email)
        return True

    changed = False
    if user.role != UserRole.ADMIN.value:
        user.role = UserRole.ADMIN.value
        changed = True
    if user.status != UserStatus.ACTIVE.value:
        user.status = UserStatus.ACTIVE.value
        changed = True
    if user.username != username:
        user.username = username
        changed = True
    if not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
        changed = True

    if changed:
        db.commit()
        logger.info("Ensured default admin user is active/admin and password-synced: %s", email)

    return changed


def ensure_default_risk_profile(
    db: Session, settings: Settings, account_id: int = 1,
) -> bool:
    """开箱确保 account_id 有 active risk_profile。

    策略调度链 (new_strategy_pipeline_job) 每轮先 _load_active_risk_profile,
    找不到就整轮 skipped —— 没有它,配好 Key 也永远不会自动决策/下单。
    生产代码此前无任何创建入口 (只有测试在建),导致新部署开箱决策链不跑。
    这里用 env 硬风控参数创建 version=1 active profile (前端后续可改)。
    """
    from src.models.account_entity import RiskProfile

    existing = (
        db.query(RiskProfile)
        .filter(RiskProfile.account_id == account_id, RiskProfile.active.is_(True))
        .first()
    )
    if existing is not None:
        return False

    profile = RiskProfile(
        account_id=account_id,
        name="default",
        max_position_size_pct=getattr(settings, "MAX_POSITION_SIZE_PCT", 0.20),
        max_daily_loss_pct=getattr(settings, "MAX_DAILY_LOSS_PCT", 0.03),
        max_consecutive_losses=getattr(settings, "MAX_CONSECUTIVE_LOSSES", 3),
        max_single_risk_pct=getattr(settings, "MAX_SINGLE_RISK_PCT", 0.01),
        version=1,
        active=True,
    )
    db.add(profile)
    db.commit()
    logger.info("Bootstrapped default active risk_profile for account_id=%s", account_id)
    return True


def ensure_default_symbol_configs(
    db: Session, settings: Settings, account_id: int = 1,
) -> int:
    """开箱 seed 交易对配置。symbol_config 表空会导致:
    - 行情自选列表(list_symbols 走 find_enabled)返回空 → 前端价格取不到 → $0.000
    - /ws/market 的 _verify_symbol_enabled 找不到 symbol → 4404 拒连
    - 决策链虽用 env PIPELINE_SYMBOLS 但配置面无交易对可管理
    生产此前无 seed 入口(只有 admin 手动加 / 测试建)。这里按 env PIPELINE_SYMBOLS
    建默认启用项。已有任意行则不动(尊重手动配置)。返回新建条数。
    """
    from src.models.symbol_config import SymbolConfig

    if db.query(SymbolConfig).count() > 0:
        return 0

    raw = getattr(settings, "PIPELINE_SYMBOLS", "") or "BTCUSDT,ETHUSDT"
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
    tf_raw = getattr(settings, "PIPELINE_TIMEFRAMES", "") or "15m"
    timeframe = (tf_raw.split(",")[0].strip() or "15m")

    created = 0
    for i, sym in enumerate(symbols):
        base = sym[:-4] if sym.endswith("USDT") else sym
        db.add(SymbolConfig(
            account_id=account_id, symbol=sym,
            base_asset=base, quote_asset="USDT",
            enabled=True, timeframe=timeframe,
            priority=100, sort_order=(i + 1) * 10,
        ))
        created += 1
    if created:
        db.commit()
        logger.info("Bootstrapped %d default symbol_configs: %s", created, symbols)
    return created


# AI 决策器默认 prompt。喂进 recent_experience_json = V0.1 的"进化"机制:
# AI 每轮都参考同 regime 的历史交易成败(ExperienceRetriever.top_k 注入)。
# 变量占位符与 PromptComposer.compose 的 variables 一一对应 (string.Template ${var})。
_AIT_DEFAULT_SYSTEM = """你是 AlphaPilot 的 AI 交易决策器,负责 Binance 现货**只做多**(V0.1 不支持做空/杠杆)。
你的唯一输出是一个 JSON 对象——不要任何解释文字,不要 markdown 代码块,不要多余字符。

# 决策原则
- 只在 regime 为 trending_up 或 ranging 且出现明确做多信号时才 OPEN_LONG。
- regime 为 chaotic(混沌)或 trending_down(下跌)时一律 HOLD,绝不开新仓。
- 已有持仓时:趋势反转或跌破风险位可 CLOSE_LONG;否则 HOLD 让利润奔跑。
- 任何非 HOLD 决策**必须**给出 stop_loss(基于 ATR,通常入场价下方 1.5~2.5×ATR)。
- 参考"同状态近期交易经验"避免重复过去的亏损模式;宁可 HOLD 也不做低胜率开仓。

# 硬约束(违反会被系统拒绝并回退 HOLD)
- action 只能是 "OPEN_LONG" | "CLOSE_LONG" | "HOLD"。
- position_size_pct ≤ 0.20(单仓位不超过账户权益 20%)。
- entry_price / stop_loss / take_profit 必须为正数;OPEN_LONG 时 stop_loss < 当前价 < take_profit。

# 输出 JSON schema
{
  "action": "OPEN_LONG|CLOSE_LONG|HOLD",
  "confidence": 0.0,
  "strategy_mode": "ai_trend|ai_breakout|ai_observation",
  "entry_type": "MARKET|LIMIT",
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "position_size_pct": 0.0,
  "reasoning": ["中文要点1", "要点2"],
  "risk_note": "一句话风险提示"
}
HOLD 时 entry_price/stop_loss/take_profit/position_size_pct 用 null, strategy_mode 用 "ai_observation"。"""

_AIT_DEFAULT_USER = """标的: ${symbol}  周期: ${timeframe}
当前价: ${current_price}
市场状态 regime: ${regime}
技术指标: ${indicators_json}
量化因子: ${factors_json}
当前持仓: ${open_position_json}
账户快照: ${account_snapshot_json}
同状态近期交易经验: ${recent_experience_json}

请基于以上信息做出本周期的交易决策,严格只输出 JSON。"""


def ensure_default_prompt_template(db: Session, settings: Settings | None = None) -> bool:
    """开箱确保有 active 的 ait_default prompt 模板。

    决策链 PromptComposer.compose 找不到 active 模板会 raise PromptTemplateNotFound,
    AITraderPipeline 兜底成 fallback_hold + decision_id=None —— 于是**不写 ai_decisions
    行、不发决策事件**,AI 决策页永远空(整轮静默,不报错)。生产此前无 seed 入口
    (只有测试建占位模板),这是 prompt_templates 空时决策不产出的根因。
    已有任意 ait_default 行则不动(尊重前端/DB 手动改的模板)。
    """
    from src.models.prompt import PromptTemplate

    exists = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.name == "ait_default")
        .count()
    )
    if exists:
        return False

    db.add(PromptTemplate(
        name="ait_default", version=1,
        system_template=_AIT_DEFAULT_SYSTEM,
        user_template=_AIT_DEFAULT_USER,
        active=True,
    ))
    db.commit()
    logger.info("Bootstrapped default active ait_default prompt_template")
    return True
