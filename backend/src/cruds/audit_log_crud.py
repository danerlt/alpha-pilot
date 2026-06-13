"""CRUD for src.models.audit_log."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.audit_log import AuditLog


class AuditLogCrud(BaseCrud[AuditLog]):
    model = AuditLog

audit_log_crud = AuditLogCrud()
