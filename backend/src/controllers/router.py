"""主 router 聚合（Stage 4 路径重组后）。

按 spec B-Hybrid 的领域子目录组织：``src/controllers/api/v1/{domain}/*.py``。
保留单一 ``router`` APIRouter 实例供 ``src.app`` 一次性 include。

兼容旧测试 ``src.controllers.router.require_admin`` 等通过本模块访问。
"""
from fastapi import APIRouter

# ── agent 域 (handoff P3) ──────────────────────────────────────────────
from src.controllers.api.v1.agent.agent import router as _agent_router

# ── execution 域 ───────────────────────────────────────────────────────
from src.controllers.api.v1.execution.account import router as _account_router
from src.controllers.api.v1.execution.orders import router as _orders_router
from src.controllers.api.v1.execution.positions import router as _positions_router
from src.controllers.api.v1.execution.trades import router as _trades_router

# ── lab 域 (handoff P5) ────────────────────────────────────────────────
from src.controllers.api.v1.lab.lab import router as _lab_router

# ── market 域 (handoff P2) ─────────────────────────────────────────────
from src.controllers.api.v1.market.market import router as _market_router

# ── risk 域 ────────────────────────────────────────────────────────────
from src.controllers.api.v1.risk.risk_events import router as _risk_router
from src.controllers.api.v1.risk.risk_state import router as _risk_state_router

# ── strategy 域 ────────────────────────────────────────────────────────
from src.controllers.api.v1.strategy.attribution import router as _attribution_router
from src.controllers.api.v1.strategy.decisions import router as _decisions_router
from src.controllers.api.v1.strategy.performance import router as _performance_router
from src.controllers.api.v1.strategy.reports import router as _reports_router
from src.controllers.api.v1.strategy.strategies import router as _strategies_router
from src.controllers.api.v1.strategy.strategy_scores import router as _strategy_scores_router

# ── system 域 ──────────────────────────────────────────────────────────
from src.controllers.api.v1.system.admin import router as _admin_router
from src.controllers.api.v1.system.auth import router as _auth_router
from src.controllers.api.v1.system.health import router as _health_router
from src.controllers.api.v1.system.runtime_config import router as _runtime_config_router
from src.controllers.api.v1.system.settings import router as _settings_router
from src.controllers.api.v1.system.tasks import router as _tasks_router

# Re-export 共享依赖（兼容老测试）
from src.controllers.dependencies import (  # noqa: F401
    _extract_bearer_token,  # deprecated 别名
    extract_bearer_token,
    get_current_user,
    require_admin,
)

router = APIRouter()
router.include_router(_health_router)
router.include_router(_auth_router)
router.include_router(_admin_router)
router.include_router(_positions_router)
router.include_router(_trades_router)
router.include_router(_decisions_router)
router.include_router(_risk_router)
router.include_router(_reports_router)
router.include_router(_strategy_scores_router)
router.include_router(_attribution_router)
router.include_router(_account_router)
router.include_router(_runtime_config_router)
router.include_router(_tasks_router)
router.include_router(_market_router)
router.include_router(_orders_router)
router.include_router(_risk_state_router)
router.include_router(_agent_router)
router.include_router(_settings_router)
router.include_router(_lab_router)
router.include_router(_performance_router)
router.include_router(_strategies_router)
