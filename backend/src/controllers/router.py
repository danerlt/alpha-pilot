"""主 router 聚合（Stage 4 路径重组后）。

按 spec B-Hybrid 的领域子目录组织：``src/controllers/api/v1/{domain}/*.py``。
保留单一 ``router`` APIRouter 实例供 ``src.app`` 一次性 include。

兼容旧测试 ``src.controllers.router.require_admin`` 等通过本模块访问。
"""
from fastapi import APIRouter

# Re-export 共享依赖（兼容老测试）
from src.controllers.dependencies import (  # noqa: F401
    _extract_bearer_token,  # deprecated 别名
    extract_bearer_token,
    get_current_user,
    require_admin,
)

# ── execution 域 ───────────────────────────────────────────────────────
from src.controllers.api.v1.execution.account import router as _account_router
from src.controllers.api.v1.execution.positions import router as _positions_router
from src.controllers.api.v1.execution.trades import router as _trades_router

# ── strategy 域 ────────────────────────────────────────────────────────
from src.controllers.api.v1.strategy.decisions import router as _decisions_router
from src.controllers.api.v1.strategy.reports import router as _reports_router

# ── risk 域 ────────────────────────────────────────────────────────────
from src.controllers.api.v1.risk.risk_events import router as _risk_router

# ── system 域 ──────────────────────────────────────────────────────────
from src.controllers.api.v1.system.admin import router as _admin_router
from src.controllers.api.v1.system.auth import router as _auth_router
from src.controllers.api.v1.system.health import router as _health_router
from src.controllers.api.v1.system.runtime_config import router as _runtime_config_router
from src.controllers.api.v1.system.tasks import router as _tasks_router

router = APIRouter()
router.include_router(_health_router)
router.include_router(_auth_router)
router.include_router(_admin_router)
router.include_router(_positions_router)
router.include_router(_trades_router)
router.include_router(_decisions_router)
router.include_router(_risk_router)
router.include_router(_reports_router)
router.include_router(_account_router)
router.include_router(_runtime_config_router)
router.include_router(_tasks_router)
