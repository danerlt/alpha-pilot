"""TaskRequest — 异步任务请求体系 (spec §4.9.1)。

前台 API 写一行 PENDING 任务并 LPUSH redis 队列, scheduler 进程 BRPOP 消费并路由到 handler。
失败时 mark_failed; scheduler 启动时 recover_orphans 把卡 RUNNING 的标 FAILED。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class TaskRequest(Base):
    __tablename__ = "task_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="任务类型, 例如 MANUAL_CLOSE_ALL")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, comment="任务参数 JSON")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True, comment="PENDING|RUNNING|SUCCESS|FAILED")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="重试次数")
    enqueued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="入队时间")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="开始执行时间")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="完成时间")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="失败原因")
    trading_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="testnet", index=True, comment="testnet|mainnet")
