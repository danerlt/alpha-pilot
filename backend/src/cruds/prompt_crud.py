"""CRUD for src.models.prompt."""
from __future__ import annotations

from src.models.prompt import PromptTemplate, ProposalDraft
from src.cruds.base_crud import BaseCrud


class PromptTemplateCrud(BaseCrud[PromptTemplate]):
    model = PromptTemplate

prompt_template_crud = PromptTemplateCrud()

class ProposalDraftCrud(BaseCrud[ProposalDraft]):
    model = ProposalDraft

proposal_draft_crud = ProposalDraftCrud()
