"""risk_events add decision_id

Revision ID: 6e79e5d8e1f6
Revises: bebb346066f0
Create Date: 2026-07-05 15:32:11.595742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e79e5d8e1f6'
down_revision: Union[str, None] = 'bebb346066f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("risk_events", sa.Column("decision_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_risk_events_decision_id", "risk_events", ["decision_id"])


def downgrade() -> None:
    op.drop_index("ix_risk_events_decision_id", table_name="risk_events")
    op.drop_column("risk_events", "decision_id")
