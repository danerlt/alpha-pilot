"""CRUD for src.models.agent_invocation."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.agent_invocation import AgentInvocation


class AgentInvocationCrud(BaseCrud[AgentInvocation]):
    model = AgentInvocation

agent_invocation_crud = AgentInvocationCrud()
