"""users add 2fa columns

Revision ID: 3970b9376189
Revises: dab932bf4b22
Create Date: 2026-07-05 21:04:01.921072

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3970b9376189'
down_revision: Union[str, None] = 'dab932bf4b22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("totp_secret", sa.String(length=300), nullable=True))
    op.add_column("users", sa.Column("two_fa_enabled", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "two_fa_enabled")
    op.drop_column("users", "totp_secret")
