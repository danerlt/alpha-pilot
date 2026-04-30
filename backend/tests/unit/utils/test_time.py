"""测试 time 工具。"""
from datetime import datetime, timedelta

from src.utils.time import TimeUtils


def test_now_returns_naive_beijing_time():
    """TimeUtils.now() 返回北京时间（naive，UTC+8）"""
    now = TimeUtils.now()
    assert isinstance(now, datetime)
    assert now.tzinfo is None  # naive，但语义是北京时间


def test_now_close_to_real_time():
    expected = datetime.utcnow() + timedelta(hours=8)
    diff = abs((TimeUtils.now() - expected).total_seconds())
    assert diff < 2  # 2 秒内
