"""CRUD for src.models.audit_log."""
from __future__ import annotations

from src.models.audit_log import AuditLog
from src.cruds.base_crud import BaseCrud


class AuditLogCrud(BaseCrud[AuditLog]):
    model = AuditLog

audit_log_crud = AuditLogCrud()
