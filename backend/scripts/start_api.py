"""API 进程入口（FastAPI + WebSocket + Redis Pub/Sub 订阅）。

scheduler / EventShuttle 由 ``scripts/start_scheduler.py`` 独占；本进程只跑 HTTP。
"""
from __future__ import annotations

import os

import uvicorn

from src.configs import get_app_config
from src.utils.log import init_logger


def main() -> None:
    init_logger("api")
    cfg = get_app_config()
    workers = int(os.getenv("UVICORN_WORKER_NUM", str(cfg.UVICORN_WORKER_NUM)))
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        reload=False,
    )


if __name__ == "__main__":
    main()
