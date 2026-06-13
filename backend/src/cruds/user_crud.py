"""CRUD for src.models.user."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.user import User


class UserCrud(BaseCrud[User]):
    model = User

user_crud = UserCrud()
