"""直接用 SQLAlchemy metadata.create_all() 建表（用于首次部署）。
后续 schema 变更再走 Alembic 迁移。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.db import get_engine
from src.models.base import Base

# 导入所有 model，确保 Base.metadata 里有完整表定义
import src.models.account      # noqa
import src.models.candle       # noqa
import src.models.decision     # noqa
import src.models.experience   # noqa
import src.models.indicator    # noqa
import src.models.order        # noqa
import src.models.position     # noqa
import src.models.regime       # noqa
import src.models.report       # noqa
import src.models.risk_event   # noqa
import src.models.trade        # noqa


def main():
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"Tables created: {list(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    main()
