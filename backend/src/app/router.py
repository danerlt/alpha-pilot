"""旧的单文件 router.py — 已拆分到 src/app/routers/* (Plan 5 cleanup)。

此文件保留为 facade 用于向后兼容 `from src.app.router import router` 的导入,
内容是把 9 个新 router 合并成一个 APIRouter 暴露。

新代码请直接 `from src.app.routers.<domain> import router as <domain>_router`,
然后在 `app.py` 里独立 include_router; 见 src/app/app.py 的示例。

Endpoints (各自所在文件):
  /                                  → routers/health.py
  /health, /api/health               → routers/health.py
  /api/auth/*                        → routers/auth.py
  /api/admin/symbols, users, audit-logs → routers/admin.py
  /api/positions/*                   → routers/positions.py
  /api/trades                        → routers/trades.py
  /api/decisions                     → routers/decisions.py
  /api/risk-events/*                 → routers/risk.py
  /api/reports/*                     → routers/reports.py
  /api/account                       → routers/account.py
"""
from fastapi import APIRouter

# Re-export 共享依赖, 兼容老测试通过 `src.app.router.require_admin` 等路径访问.
from src.app.dependencies import (  # noqa: F401
    _extract_bearer_token,  # deprecated 别名, 新代码用 extract_bearer_token
    extract_bearer_token,
    get_current_user,
    require_admin,
)
from src.app.routers.account import router as _account_router
from src.app.routers.admin import router as _admin_router
from src.app.routers.auth import router as _auth_router
from src.app.routers.decisions import router as _decisions_router
from src.app.routers.health import router as _health_router
from src.app.routers.positions import router as _positions_router
from src.app.routers.reports import router as _reports_router
from src.app.routers.risk import router as _risk_router
from src.app.routers.trades import router as _trades_router

# 把 9 个 domain router 合并; app.py 仍然可以 `include_router(router)`.
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
