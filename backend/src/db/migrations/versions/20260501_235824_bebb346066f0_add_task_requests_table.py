"""add task_requests table

Revision ID: bebb346066f0
Revises: 602c525cfbcd
Create Date: 2026-05-01 23:58:24.067286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bebb346066f0'
down_revision: Union[str, None] = '602c525cfbcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
        sa.Column('task_type', sa.String(length=64), nullable=False, comment='任务类型, 例如 MANUAL_CLOSE_ALL'),
        sa.Column('payload', sa.JSON(), nullable=False, comment='任务参数 JSON'),
        sa.Column('status', sa.String(length=16), nullable=False, comment='PENDING|RUNNING|SUCCESS|FAILED'),
        sa.Column('attempts', sa.Integer(), nullable=False, comment='重试次数'),
        sa.Column('enqueued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='入队时间'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始执行时间'),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='失败原因'),
        sa.Column('trading_mode', sa.String(length=16), nullable=False, comment='testnet|mainnet'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='记录创建时间（UTC）'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='记录最后更新时间（UTC）'),
        sa.Column('enable_flag', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False, comment='是否有效（False=禁用，业务过滤用）'),
        sa.Column('delete_flag', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False, comment='是否软删（True=已删除，物理保留）'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('PENDING','RUNNING','SUCCESS','FAILED')", name='ck_task_requests_status'),
    )
    op.create_index('ix_task_requests_task_type', 'task_requests', ['task_type'], unique=False)
    op.create_index('ix_task_requests_status', 'task_requests', ['status'], unique=False)
    op.create_index('ix_task_requests_trading_mode', 'task_requests', ['trading_mode'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_task_requests_trading_mode', table_name='task_requests')
    op.drop_index('ix_task_requests_status', table_name='task_requests')
    op.drop_index('ix_task_requests_task_type', table_name='task_requests')
    op.drop_table('task_requests')
