"""CRUD for src.models.user."""
from __future__ import annotations

from src.models.user import User
from src.cruds.base_crud import BaseCrud


class UserCrud(BaseCrud[User]):
    model = User

user_crud = UserCrud()
