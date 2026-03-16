"""直接用 SQLAlchemy metadata.create_all() 建表（用于首次部署）。
后续 schema 变更再走 Alembic 迁移。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.db import get_engine
from src.shared.models.base import Base

# 导入所有 model，确保 Base.metadata 里有完整表定义
import src.shared.models.account      # noqa
import src.shared.models.candle       # noqa
import src.shared.models.decision     # noqa
import src.shared.models.experience   # noqa
import src.shared.models.indicator    # noqa
import src.shared.models.order        # noqa
import src.shared.models.position     # noqa
import src.shared.models.regime       # noqa
import src.shared.models.report       # noqa
import src.shared.models.risk_event   # noqa
import src.shared.models.trade        # noqa


def main():
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"Tables created: {list(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    main()
