"""add_event_outbox_event_id_index

Revision ID: bbe8a491f942
Revises: b338184343a4
Create Date: 2026-04-26 14:08:58.444267

post-Plan5 codereview Risk #6: GET /api/events/catchup 和 WebSocket
_replay_since 都跑 `WHERE published_at IS NOT NULL AND event_id > since
ORDER BY id ASC LIMIT N`. 没有 (event_id) 索引时 → 全表扫. 生产事件量
起来后会显著拖慢 catchup / WebSocket 重连. 加单列 b-tree 索引.

published_at 部分索引也有用但 V0.1 单进程量级不必, 等 V0.2 再优化.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbe8a491f942'
down_revision: Union[str, None] = 'b338184343a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_event_outbox_event_id",
        "event_outbox",
        ["event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_event_outbox_event_id", table_name="event_outbox")
