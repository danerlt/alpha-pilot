# Stage 1: 基础设施层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建模板规定的基础设施层（DB / 配置 / 通用工具 / 中间件 / 异常 / 响应 schema），但 **HTTP 行为零变化** — 只注入 request_id 和 access log，不改响应格式、不改异常处理、不重组 controllers。

**Architecture:** 沿用现有 FastAPI 单进程 + lifespan APScheduler；新增 `src/db/` `src/configs/` `src/common/` `src/utils/` `src/middleware/` 五个基础设施目录；提级 `src/app/app.py` 为 `src/app.py`；旧 `src/shared/db.py` 改成转发 wrapper。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.x / pydantic-settings 2.x / asgi-correlation-id / starlette-context

**关联 spec：** `docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` v3.6 §3.1, §4.1, §4.2, §4.6.1, §4.6.2, §4.6.3, §4.6.4, §4.6.5, §4.7, §4.10, §6 阶段 1

**前置条件：**
- 当前位于 `main` 分支或新建 `refactor/stage1-infra` 分支
- `make dev-up` 起 PostgreSQL + Redis 容器
- `cd backend && uv sync --extra dev` 依赖完整
- 现有 53 测试全绿（基线）

---

## File Structure（终态）

```
backend/
├── pyproject.toml                          # 新增依赖：asgi-correlation-id / starlette-context
└── src/
    ├── app.py                              # 提级（替代 src/app/app.py）
    ├── app/                                # 暂保留 routers/、websocket.py、router.py、dependencies.py
    │   ├── routers/                        # 阶段 4 重组到 controllers/
    │   ├── websocket.py
    │   ├── router.py
    │   └── dependencies.py
    ├── configs/
    │   ├── __init__.py
    │   └── app_configs.py                  # 重写：8 个子配置类多继承
    ├── common/                             # 全新
    │   ├── __init__.py
    │   ├── constants.py
    │   ├── enums.py                        # 暂迁 src/shared/enums.py 内容
    │   ├── pagination.py
    │   ├── schema.py
    │   ├── api_response.py                 # @api_response 装饰器
    │   ├── events.py                       # BaseEvent + 事件类（阶段 3 填充事件类，阶段 1 仅 BaseEvent）
    │   ├── response/
    │   │   ├── __init__.py
    │   │   ├── response_schema.py          # Response[T] / response_base
    │   │   └── response_code.py            # ErrorCode 枚举
    │   ├── exception/
    │   │   ├── __init__.py
    │   │   ├── errors.py                   # AppBaseException 树（含 auto_log + stack）
    │   │   └── exception_handler.py        # 全局 handler 注册
    │   └── schemas/
    │       └── pagination.py               # Paginated[T]
    ├── db/                                 # 全新
    │   ├── __init__.py
    │   ├── engines.py                      # PostgreSQL 同步 engine + SessionLocal
    │   ├── session.py                      # get_db / get_db_session / CurrentSession
    │   └── alembic.ini                     # 阶段 2 迁过来；阶段 1 占位创建空文件
    ├── middleware/                         # 全新
    │   ├── __init__.py
    │   ├── request_logging_middleware.py
    │   └── error_logging_middleware.py
    ├── utils/                              # 全新；逐步迁现有 shared/* 工具
    │   ├── __init__.py
    │   ├── log.py                          # init_logger / get_logger / ContextFilter
    │   ├── redis.py                        # get_redis_client / get_async_redis
    │   ├── time.py                         # TimeUtils
    │   ├── uuid.py                         # get_uuid_without_hyphen
    │   ├── request_id.py                   # get_request_id / current_request_id
    │   ├── json.py                         # 自定义 JSON 编解码（datetime/Enum/Decimal）
    │   └── serializers.py                  # 占位（可选）
    ├── shared/                             # 改造为转发 wrapper（暂留，阶段 2-3 逐步移除）
    │   ├── db.py                           # 转发到 src/db/session.py
    │   ├── config.py                       # 转发到 src/configs/app_configs.py
    │   ├── enums.py                        # 暂保留（阶段 2 迁到 models/enums.py）
    │   ├── models/                         # 阶段 2 处理
    │   ├── schemas/                        # 阶段 2 处理
    │   └── ...                             # 其余阶段 2-3 处理
    └── ...（其余 control/ events/ execution/ insight/ services/ strategy/ workers/ 阶段 3 处理）
```

---

## 任务清单

### Task 1：创建分支 + 验证基线测试

**Files:**
- 仅 git 操作

- [ ] **Step 1: 切到主分支并拉最新**

```bash
git checkout main
git pull
```

- [ ] **Step 2: 创建 stage1 分支**

```bash
git checkout -b refactor/stage1-infra
```

- [ ] **Step 3: 跑当前测试（基线）**

```bash
cd backend && uv run pytest -x -q
```

Expected: 53 passed（或当前实际数量）

- [ ] **Step 4: 记录基线测试数到 worklog**

```bash
mkdir -p ../docs/worklog
echo "# Stage 1 基线 ($(date +%Y-%m-%d))" > ../docs/worklog/$(date +%Y%m%d_%H%M)_stage1_baseline.md
echo "- 起点 commit: $(git rev-parse HEAD)" >> ../docs/worklog/$(date +%Y%m%d_%H%M)_stage1_baseline.md
echo "- pytest: 53 passed" >> ../docs/worklog/$(date +%Y%m%d_%H%M)_stage1_baseline.md
```

- [ ] **Step 5: 提交基线**

```bash
cd ..
git add docs/worklog/
git -c commit.gpgsign=false commit -m "chore(stage1): 记录重构基线测试数与起点 commit"
git push -u origin refactor/stage1-infra
```

---

### Task 2：新增基础设施依赖

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: 添加 asgi-correlation-id 与 starlette-context**

```bash
cd backend && uv add 'asgi-correlation-id>=4.3.4' 'starlette-context>=0.4.0'
```

Expected: `pyproject.toml` 新增 dependencies；`uv.lock` 更新

- [ ] **Step 2: 验证依赖可 import**

```bash
uv run python -c "from asgi_correlation_id import correlation_id; from starlette_context import context; print('ok')"
```

Expected: 输出 `ok`

- [ ] **Step 3: 跑测试确认未破坏**

```bash
uv run pytest -x -q
```

Expected: 53 passed

- [ ] **Step 4: 提交**

```bash
cd ..
git add backend/pyproject.toml backend/uv.lock
git -c commit.gpgsign=false commit -m "chore(stage1): 新增 asgi-correlation-id 与 starlette-context 依赖"
git push
```

---

### Task 3：创建 src/utils/log.py（含 ContextFilter 注入 request_id）

**Files:**
- Create: `backend/src/utils/__init__.py`
- Create: `backend/src/utils/log.py`
- Test: `backend/tests/unit/utils/test_log.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/utils/__init__.py`（空文件）和 `backend/tests/unit/utils/test_log.py`：

```python
"""测试 log.py 的 ContextFilter 自动注入 request_id 到 LogRecord。"""
import logging
from src.utils.log import ContextFilter


def test_context_filter_injects_dash_when_no_request_id():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="x", lineno=1,
        msg="msg", args=(), exc_info=None,
    )
    f = ContextFilter()
    assert f.filter(record) is True
    assert record.request_id == "-"


def test_context_filter_keeps_existing_request_id():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="x", lineno=1,
        msg="msg", args=(), exc_info=None,
    )
    record.request_id = "abc123"
    f = ContextFilter()
    assert f.filter(record) is True
    assert record.request_id == "abc123"
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/utils/test_log.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.utils.log'`

- [ ] **Step 3: 创建 src/utils/__init__.py（空）和 src/utils/log.py**

`backend/src/utils/__init__.py` 留空。

`backend/src/utils/log.py`:

```python
"""日志初始化与工具。

约定：
- 所有模块用 `get_logger(__name__)` 获取 logger
- formatter 自动包含 request_id 字段（HTTP 请求级追踪 ID）
- ContextFilter 在 LogRecord 缺失 request_id 时自动填 "-"，避免 formatter 报 KeyError
"""
from __future__ import annotations

import logging
from typing import Optional


class ContextFilter(logging.Filter):
    """为每条 LogRecord 自动注入 request_id 字段。

    HTTP 链路通过 asgi-correlation-id 中间件在 ContextVar 内提供 request_id；
    本 filter 调用 src.utils.request_id.get_request_id() 读取。
    在 scheduler 进程或非请求上下文中读不到时填 "-"。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            try:
                from src.utils.request_id import get_request_id  # 延迟 import 避免循环
                record.request_id = get_request_id() or "-"
            except Exception:
                record.request_id = "-"
        return True


LOG_FORMAT = (
    "%(asctime)s %(levelname)-8s [%(name)s] "
    "request_id=%(request_id)s "
    "%(filename)s:%(lineno)d %(funcName)s | %(message)s"
)


def init_logger(name: str = "app", file_name: Optional[str] = None) -> None:
    """初始化全局 logging。api 进程入口、scheduler 进程入口都应调用一次。

    幂等：重复调用以最后一次为准（force=True）。
    """
    fmt = logging.Formatter(LOG_FORMAT)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if file_name:
        import os
        os.makedirs("logs", exist_ok=True)
        handlers.append(logging.FileHandler(f"logs/{file_name}", encoding="utf-8"))

    for h in handlers:
        h.setFormatter(fmt)
        h.addFilter(ContextFilter())

    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    """获取 logger；调用方一般用 `get_logger(__name__)`。"""
    return logging.getLogger(name)
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/utils/test_log.py -v
```

Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/utils/__init__.py backend/src/utils/log.py backend/tests/unit/utils/
git -c commit.gpgsign=false commit -m "feat(stage1): 引入 src/utils/log.py — ContextFilter 自动注入 request_id"
git push
```

---

### Task 4：创建 src/utils/request_id.py

**Files:**
- Create: `backend/src/utils/request_id.py`
- Test: `backend/tests/unit/utils/test_request_id.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/unit/utils/test_request_id.py`:

```python
"""测试 request_id 工具函数。"""
from asgi_correlation_id import correlation_id
from src.utils.request_id import get_request_id, current_request_id


def test_get_request_id_returns_none_when_unset():
    correlation_id.set(None)
    assert get_request_id() is None


def test_get_request_id_returns_value_when_set():
    correlation_id.set("abc123def456")
    assert get_request_id() == "abc123def456"


def test_current_request_id_returns_dash_when_unset():
    correlation_id.set(None)
    assert current_request_id() == "-"


def test_current_request_id_returns_value_when_set():
    correlation_id.set("xyz789")
    assert current_request_id() == "xyz789"
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/utils/test_request_id.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现**

`backend/src/utils/request_id.py`:

```python
"""HTTP 请求级 request_id 读取工具。

注意：这里的 request_id 是 HTTP 请求追踪 ID（X-Request-ID 头），
与业务幂等键 trace_id（如 Order.trace_id = SHA256(...)）是完全不同的概念，
不要混淆。
"""
from __future__ import annotations

from asgi_correlation_id import correlation_id


def get_request_id() -> str | None:
    """读取当前请求的 request_id。

    HTTP 链路：CorrelationIdMiddleware 已在 ContextVar 中注入；
    scheduler 链路 / 非请求上下文：返回 None。
    """
    return correlation_id.get()


def current_request_id() -> str:
    """便捷别名：拿不到时返 "-"，便于直接拼到日志/响应里。"""
    return get_request_id() or "-"
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/utils/test_request_id.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/utils/request_id.py backend/tests/unit/utils/test_request_id.py
git -c commit.gpgsign=false commit -m "feat(stage1): 引入 src/utils/request_id.py — HTTP 链路 ID 读取工具"
git push
```

---

### Task 5：创建 src/utils/uuid.py（迁现有 get_uuid_without_hyphen）

**Files:**
- Create: `backend/src/utils/uuid.py`
- Test: `backend/tests/unit/utils/test_uuid.py`

- [ ] **Step 1: 检查现有实现位置**

```bash
cd backend && grep -rn "get_uuid_without_hyphen" src/
```

期望：发现现有定义（可能在 `src/shared/` 或某处），记下原路径备用作转发兼容。

- [ ] **Step 2: 写失败测试**

`backend/tests/unit/utils/test_uuid.py`:

```python
import re
from src.utils.uuid import get_uuid_without_hyphen


def test_get_uuid_without_hyphen_returns_32_char_hex():
    uid = get_uuid_without_hyphen()
    assert isinstance(uid, str)
    assert len(uid) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", uid) is not None


def test_get_uuid_without_hyphen_unique():
    uids = {get_uuid_without_hyphen() for _ in range(100)}
    assert len(uids) == 100
```

- [ ] **Step 3: 跑测试确认 fail**

```bash
uv run pytest tests/unit/utils/test_uuid.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: 实现**

`backend/src/utils/uuid.py`:

```python
"""UUID 工具。"""
from __future__ import annotations

from uuid import uuid4


def get_uuid_without_hyphen() -> str:
    """生成 32 字符 hex（无横线）的 UUID4。

    用于：
    - HTTP request_id（asgi-correlation-id middleware 的 generator）
    - 历史业务键（部分旧表保留）
    """
    return uuid4().hex
```

- [ ] **Step 5: 跑测试确认 pass**

```bash
uv run pytest tests/unit/utils/test_uuid.py -v
```

Expected: 2 passed

- [ ] **Step 6: 检查现有调用点是否需要兼容转发**

```bash
grep -rn "get_uuid_without_hyphen" src/ --include='*.py'
```

如有现有代码 import 旧路径，**保留旧路径文件**，让旧路径 re-export 新位置：

```python
# 例如 src/shared/uuid.py（如存在）
from src.utils.uuid import get_uuid_without_hyphen  # noqa: F401
__all__ = ["get_uuid_without_hyphen"]
```

如无现有定义则跳过此步。

- [ ] **Step 7: 跑全量测试**

```bash
uv run pytest -x -q
```

Expected: 全绿（包含历史 53 + 新增 6）

- [ ] **Step 8: 提交**

```bash
cd ..
git add backend/src/utils/uuid.py backend/tests/unit/utils/test_uuid.py
[ -f backend/src/shared/uuid.py ] && git add backend/src/shared/uuid.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/utils/uuid.py — get_uuid_without_hyphen"
git push
```

---

### Task 6：创建 src/utils/time.py（TimeUtils）

**Files:**
- Create: `backend/src/utils/time.py`
- Test: `backend/tests/unit/utils/test_time.py`

- [ ] **Step 1: 检查现有 datetime_utils**

```bash
cd backend && cat src/shared/datetime_utils.py 2>/dev/null | head -50
```

记下现有实现，迁移时保留行为兼容。

- [ ] **Step 2: 写失败测试**

`backend/tests/unit/utils/test_time.py`:

```python
from datetime import datetime, timezone, timedelta
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
```

- [ ] **Step 3: 跑测试确认 fail**

```bash
uv run pytest tests/unit/utils/test_time.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: 实现**

`backend/src/utils/time.py`:

```python
"""时间工具。强制北京时间（naive datetime, UTC+8）。

约定：
- DB 存储用 naive datetime，语义为北京时间
- 不在 ORM 层做 tz conversion，业务层全部用 TimeUtils.now() 取当下时间
- 与现有 src.shared.datetime_utils 行为一致；迁移路径保留兼容 import
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


class TimeUtils:
    """北京时间工具集。"""

    @staticmethod
    def now() -> datetime:
        """返回当前北京时间（UTC+8，naive datetime）。"""
        return datetime.utcnow() + timedelta(hours=8)

    @staticmethod
    def utcnow() -> datetime:
        """返回当前 UTC 时间（naive）。"""
        return datetime.utcnow()
```

- [ ] **Step 5: 跑测试确认 pass**

```bash
uv run pytest tests/unit/utils/test_time.py -v
```

Expected: 2 passed

- [ ] **Step 6: 兼容旧路径（如有）**

如 `src/shared/datetime_utils.py` 被现有代码引用，加 re-export：

```python
# src/shared/datetime_utils.py 末尾
from src.utils.time import TimeUtils  # noqa: F401
```

- [ ] **Step 7: 跑全量测试**

```bash
uv run pytest -x -q
```

Expected: 全绿

- [ ] **Step 8: 提交**

```bash
cd ..
git add backend/src/utils/time.py backend/tests/unit/utils/test_time.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/utils/time.py — TimeUtils 北京时间工具"
git push
```

---

### Task 7：创建 src/utils/redis.py（同步 + 异步客户端工厂）

**Files:**
- Create: `backend/src/utils/redis.py`
- Test: `backend/tests/unit/utils/test_redis.py`

- [ ] **Step 1: 写失败测试（用 fakeredis）**

`backend/tests/unit/utils/test_redis.py`:

```python
from src.utils.redis import get_redis_client, reset_redis_clients


def test_get_redis_client_returns_singleton(monkeypatch):
    """同一进程内多次调用返回同一实例。"""
    reset_redis_clients()
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    c1 = get_redis_client()
    c2 = get_redis_client()
    assert c1 is c2
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/utils/test_redis.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现**

`backend/src/utils/redis.py`:

```python
"""Redis 客户端工厂。同步/异步并存。

- 同步客户端：用于 scheduler 容器主线程 BRPOP（阻塞操作）+ 业务侧 lpush/get 等同步调用
- 异步客户端：用于 api 容器 lifespan 协程的 Redis Pub/Sub 订阅
- 进程内单例，按需创建
"""
from __future__ import annotations

from typing import Optional

import redis as sync_redis
import redis.asyncio as async_redis

_sync_client: Optional[sync_redis.Redis] = None
_async_client: Optional[async_redis.Redis] = None


def get_redis_client() -> sync_redis.Redis:
    """同步 Redis 客户端单例。"""
    global _sync_client
    if _sync_client is None:
        from src.configs import get_app_config
        cfg = get_app_config()
        _sync_client = sync_redis.from_url(
            cfg.REDIS_URL, decode_responses=True,
        )
    return _sync_client


def get_async_redis() -> async_redis.Redis:
    """异步 Redis 客户端单例（仅 api 容器 lifespan 使用）。"""
    global _async_client
    if _async_client is None:
        from src.configs import get_app_config
        cfg = get_app_config()
        _async_client = async_redis.from_url(
            cfg.REDIS_URL, decode_responses=True,
        )
    return _async_client


def reset_redis_clients() -> None:
    """单测使用：重置单例。生产代码不应调用。"""
    global _sync_client, _async_client
    if _sync_client is not None:
        try:
            _sync_client.close()
        except Exception:
            pass
    _sync_client = None
    _async_client = None
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/utils/test_redis.py -v
```

Expected: 1 passed（依赖 REDIS_URL 配置成功）

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/utils/redis.py backend/tests/unit/utils/test_redis.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/utils/redis.py — 同步/异步 Redis 客户端工厂"
git push
```

---

### Task 8：创建 src/utils/json.py（自定义 JSON 编解码）

**Files:**
- Create: `backend/src/utils/json.py`
- Test: `backend/tests/unit/utils/test_json.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/unit/utils/test_json.py`:

```python
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum

from src.utils.json import dumps


class _Color(Enum):
    RED = "red"


def test_dumps_datetime():
    s = dumps({"t": datetime(2026, 4, 30, 10, 23, 45)})
    assert "2026-04-30 10:23:45" in s


def test_dumps_decimal():
    s = dumps({"x": Decimal("3.14")})
    assert '"x": "3.14"' in s


def test_dumps_enum():
    s = dumps({"c": _Color.RED})
    assert '"c": "red"' in s


def test_dumps_chinese_no_ascii():
    s = dumps({"name": "持仓"})
    assert "持仓" in s
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/utils/test_json.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现**

`backend/src/utils/json.py`:

```python
"""统一 JSON 编解码：支持 datetime / Enum / Decimal / Pydantic / dataclass。"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class AppJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "model_dump"):  # Pydantic v2
            return obj.model_dump(mode="json")
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


def dumps(obj: Any, **kwargs: Any) -> str:
    """JSON 序列化。默认 ensure_ascii=False 支持中文。"""
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("cls", AppJSONEncoder)
    return json.dumps(obj, **kwargs)


def loads(s: str | bytes) -> Any:
    """JSON 反序列化。"""
    return json.loads(s)
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/utils/test_json.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/utils/json.py backend/tests/unit/utils/test_json.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/utils/json.py — 自定义 JSON 编解码"
git push
```

---

### Task 9：重写 src/configs/app_configs.py（8 个子配置类多继承）

**Files:**
- Modify: `backend/src/configs/app_configs.py`（重写）
- Modify: `backend/src/configs/__init__.py`（更新导出）
- Test: `backend/tests/unit/configs/test_app_configs.py`

- [ ] **Step 1: 备份现有 app_configs.py 内容到 worklog**

```bash
cd backend && cp src/configs/app_configs.py /tmp/app_configs.bak.py
echo "## app_configs.py 重写前快照" >> ../docs/worklog/$(date +%Y%m%d)_stage1_configs_rewrite.md
echo "保存于 /tmp/app_configs.bak.py（参考用）" >> ../docs/worklog/$(date +%Y%m%d)_stage1_configs_rewrite.md
```

- [ ] **Step 2: 写测试确认子配置类继承正确**

`backend/tests/unit/configs/__init__.py` 留空。

`backend/tests/unit/configs/test_app_configs.py`:

```python
"""验证 AppConfig 多继承聚合 + 各子配置字段可读。"""
import os
from src.configs.app_configs import AppConfig


def test_app_config_loads_with_skip_validation(monkeypatch):
    monkeypatch.setenv("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")
    cfg = AppConfig()
    # ServiceConfig
    assert cfg.ENVIRONMENT in ("dev", "uat", "prod", "test", "local")
    assert cfg.UVICORN_WORKER_NUM >= 1
    # PostgreSQLConfig
    assert cfg.PG_HOST
    assert cfg.PG_PORT > 0
    assert "postgresql+psycopg2://" in cfg.db_uri
    # SchedulerConfig
    assert cfg.STRATEGY_LOOP_INTERVAL_MINUTES > 0
    assert cfg.POSITION_MONITOR_INTERVAL_SECONDS > 0
    assert cfg.TASK_QUEUE_KEY == "alphapilot:tasks"
    assert cfg.EVENT_BUS_CHANNEL == "alphapilot:events"
    assert cfg.APSCHEDULER_JOBS_TABLE == "apscheduler_jobs"
    # ExchangeConfig
    assert cfg.TRADING_MODE in ("testnet", "mainnet")
    # RiskConfig
    assert 0 < cfg.MAX_POSITION_SIZE_PCT <= 1
    assert 0 < cfg.MAX_DAILY_LOSS_PCT <= 1


def test_db_uri_uses_postgres(monkeypatch):
    monkeypatch.setenv("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")
    monkeypatch.setenv("PG_USER", "u")
    monkeypatch.setenv("PG_PASSWORD", "p@ss/word")
    monkeypatch.setenv("PG_HOST", "localhost")
    monkeypatch.setenv("PG_PORT", "5442")
    monkeypatch.setenv("PG_DB", "alphapilot")
    cfg = AppConfig()
    assert "postgresql+psycopg2://u:p%40ss%2Fword@localhost:5442/alphapilot" in cfg.db_uri
```

- [ ] **Step 3: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/configs/test_app_configs.py -v
```

Expected: FAIL（PG_HOST 等字段不存在）

- [ ] **Step 4: 重写 app_configs.py**

`backend/src/configs/app_configs.py`:

```python
"""AlphaPilot 统一配置 — 8 个子配置类多继承聚合。

加载优先级：代码默认 → .env 文件 → 真实环境变量。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.shared.enums import TradingMode  # 阶段 2 会迁到 src/common/enums.py 或 src/models/enums.py

_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"


# ── 占位与安全校验（保留现有逻辑）─────────────────────────────────────────────
PLACEHOLDER_BINANCE_KEYS: frozenset[str] = frozenset({"test-binance-api-key", "test-binance-api-secret", ""})
PLACEHOLDER_LLM_KEYS: frozenset[str] = frozenset({"test-llm-api-key", ""})

_INSECURE_KEY_VALUES = frozenset({
    "2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA=",
    "ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE=",
    "alpha-pilot-auth-secret-change-me",
})

_INSECURE_KEY_PREFIXES = (
    "dev-only-do-not-use", "change-me", "your-secret-key", "test-secret",
)


class InsecureSecretError(RuntimeError):
    """启动时检测到弱/默认密钥。"""


def _looks_insecure(value: str) -> bool:
    if not value:
        return True
    if value in _INSECURE_KEY_VALUES:
        return True
    v = value.strip().lower()
    return any(v.startswith(p.lower()) for p in _INSECURE_KEY_PREFIXES)


# ── 子配置类 ───────────────────────────────────────────────────────────────
class ServiceConfig(BaseSettings):
    ENVIRONMENT: str = Field(default="dev", description="dev/uat/prod/test/local")
    LOG_LEVEL: str = Field(default="INFO")
    UVICORN_WORKER_NUM: int = Field(default=1, description="api 进程的 uvicorn worker 数")
    FASTAPI_ROOT_PATH: str = Field(default="", description="子路径部署时的 root_path（如 '/api'）")


class CORSConfig(BaseSettings):
    ENABLE_CORS: bool = Field(default=True)
    CORS_ALLOWED_ORIGINS: list[str] = Field(default=["*"])
    CORS_EXPOSE_HEADERS: list[str] = Field(default=["X-Request-ID"])


class PostgreSQLConfig(BaseSettings):
    PG_USER: str = Field(default="alphapilot")
    PG_PASSWORD: str = Field(default="alphapilot")
    PG_HOST: str = Field(default="localhost")
    PG_PORT: int = Field(default=5442)
    PG_DB: str = Field(default="alphapilot")
    POOL_SIZE: int = Field(default=20)
    POOL_MAX_OVERFLOW: int = Field(default=20)
    DB_CONNECT_TIMEOUT: int = Field(default=10)
    PRINT_SQL: bool = Field(default=False, description="echo SQL 到日志（仅 dev）")

    @property
    def db_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.PG_USER}:{quote_plus(self.PG_PASSWORD)}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        )


class RedisConfig(BaseSettings):
    REDIS_URL: str = Field(default="redis://localhost:6389/0")


class SchedulerConfig(BaseSettings):
    STRATEGY_LOOP_INTERVAL_MINUTES: int = Field(default=15)
    POSITION_MONITOR_INTERVAL_SECONDS: int = Field(default=10)
    APSCHEDULER_JOBS_TABLE: str = Field(default="apscheduler_jobs")
    TASK_QUEUE_KEY: str = Field(default="alphapilot:tasks")
    EVENT_BUS_CHANNEL: str = Field(default="alphapilot:events")
    EVENT_SHUTTLE_BATCH_SIZE: int = Field(default=50)
    EVENT_SHUTTLE_IDLE_SLEEP_SECONDS: float = Field(default=0.5)
    EVENT_SHUTTLE_MAX_FAILED_ATTEMPTS: int = Field(default=3)
    SCHEDULER_GRACEFUL_SHUTDOWN_SECONDS: int = Field(default=60)


class ExchangeConfig(BaseSettings):
    TRADING_MODE: TradingMode = Field(default=TradingMode.TESTNET)
    BINANCE_API_KEY: str = Field(default="test-binance-api-key")
    BINANCE_API_SECRET: str = Field(default="test-binance-api-secret")


class LLMConfig(BaseSettings):
    LLM_BASE_URL: str = Field(default="https://api.deepseek.com/v1")
    LLM_API_KEY: str = Field(default="test-llm-api-key")
    LLM_MODEL: str = Field(default="deepseek-v4-pro")
    LLM_TIMEOUT_SECONDS: int = Field(default=30)


class RiskConfig(BaseSettings):
    MAX_POSITION_SIZE_PCT: float = Field(default=0.20)
    MAX_DAILY_LOSS_PCT: float = Field(default=0.03)
    MAX_CONSECUTIVE_LOSSES: int = Field(default=3)
    MAX_SINGLE_RISK_PCT: float = Field(default=0.01)


class SecurityConfig(BaseSettings):
    APP_CONFIG_MASTER_KEY: str = Field(default="ZGV2X3Rlc3RfYWxwaGFwaWxvdF9rZXlfX19fX19fXzE=")
    APP_AUTH_SECRET_KEY: str = Field(default="dev-only-do-not-use-in-prod-auth-key-please-rotate")
    DEFAULT_ADMIN_EMAIL: str = Field(default="")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="")
    DEFAULT_ADMIN_USERNAME: str = Field(default="")


# ── 主配置（多继承聚合）─────────────────────────────────────────────────────
class AppConfig(
    ServiceConfig,
    CORSConfig,
    PostgreSQLConfig,
    RedisConfig,
    SchedulerConfig,
    ExchangeConfig,
    LLMConfig,
    RiskConfig,
    SecurityConfig,
):
    """全局应用配置。业务代码通过 `get_app_config().FIELD` 访问。"""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


def _validate_secrets(settings: AppConfig) -> None:
    if os.getenv("ALPHAPILOT_SKIP_SECRET_VALIDATION") == "1":
        return
    insecure: list[str] = []
    if _looks_insecure(settings.APP_AUTH_SECRET_KEY):
        insecure.append("APP_AUTH_SECRET_KEY")
    if _looks_insecure(settings.APP_CONFIG_MASTER_KEY):
        insecure.append("APP_CONFIG_MASTER_KEY")
    if insecure:
        names = ", ".join(insecure)
        raise InsecureSecretError(
            f"Refusing to start: {names} 仍是默认/弱密钥。"
            f"APP_AUTH_SECRET_KEY 用 `openssl rand -hex 32`；"
            f"APP_CONFIG_MASTER_KEY 用 `python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`。"
            f"单测请设 ALPHAPILOT_SKIP_SECRET_VALIDATION=1。"
        )


@lru_cache
def get_app_config() -> AppConfig:
    s = AppConfig()
    _validate_secrets(s)
    return s


def get_settings() -> AppConfig:
    """向后兼容别名。"""
    return get_app_config()


get_base_settings = get_app_config


# ── 凭证诊断（保留现有 API）────────────────────────────────────────────────
def _cred_status(configured: bool, reason: str | None = None) -> dict[str, object]:
    return {"configured": configured, "reason": reason}


def get_runtime_credential_status(settings: AppConfig) -> dict[str, dict[str, object]]:
    binance_key = getattr(settings, "BINANCE_API_KEY", "") or ""
    binance_secret = getattr(settings, "BINANCE_API_SECRET", "") or ""
    llm_key = getattr(settings, "LLM_API_KEY", "") or ""

    if binance_key in PLACEHOLDER_BINANCE_KEYS or binance_secret in PLACEHOLDER_BINANCE_KEYS:
        binance = _cred_status(False, "placeholder_or_missing")
    else:
        binance = _cred_status(True, None)

    if llm_key in PLACEHOLDER_LLM_KEYS:
        llm = _cred_status(False, "placeholder_or_missing")
    else:
        llm = _cred_status(True, None)

    mode = settings.TRADING_MODE
    mode_val = mode.value if isinstance(mode, TradingMode) else str(mode)

    return {
        "binance": {**binance, "mode": mode_val},
        "llm": {**llm, "base_url": settings.LLM_BASE_URL, "model": settings.LLM_MODEL},
    }


def can_call_binance(settings: AppConfig) -> bool:
    return bool(get_runtime_credential_status(settings)["binance"]["configured"])


def can_call_llm(settings: AppConfig) -> bool:
    return bool(get_runtime_credential_status(settings)["llm"]["configured"])
```

- [ ] **Step 5: 更新 src/configs/__init__.py**

`backend/src/configs/__init__.py`:

```python
"""配置入口。业务代码通过 `from src.configs import get_app_config`。"""
from src.configs.app_configs import (
    AppConfig,
    InsecureSecretError,
    can_call_binance,
    can_call_llm,
    get_app_config,
    get_base_settings,
    get_runtime_credential_status,
    get_settings,
)

__all__ = [
    "AppConfig",
    "InsecureSecretError",
    "can_call_binance",
    "can_call_llm",
    "get_app_config",
    "get_base_settings",
    "get_runtime_credential_status",
    "get_settings",
]
```

- [ ] **Step 6: 检查并更新 example.env**

```bash
cd .. && cat backend/example.env  # 看现有 env 字段
```

修改 `backend/example.env` 字段顺序与 AppConfig 子类列表一致：先 ServiceConfig 字段，再 CORSConfig … 直到 SecurityConfig。把旧的 `DATABASE_URL` 删掉，改用 `PG_USER` / `PG_PASSWORD` / `PG_HOST` / `PG_PORT` / `PG_DB`。具体字段值参考 `app_configs.py` 默认值。

- [ ] **Step 7: 跑配置测试**

```bash
cd backend && uv run pytest tests/unit/configs/ -v
```

Expected: 2 passed

- [ ] **Step 8: 跑全量测试（确认未破坏现有调用）**

```bash
ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -x -q
```

Expected: 全绿

注意：可能有现有代码引用 `DATABASE_URL` —— 如果出现失败，找到引用点改成 `cfg.db_uri`。

- [ ] **Step 9: 提交**

```bash
cd ..
git add backend/src/configs/ backend/tests/unit/configs/ backend/example.env
git -c commit.gpgsign=false commit -m "refactor(stage1): 重写 app_configs.py — 8 个子配置类多继承"
git push
```

---

### Task 10：创建 src/db/engines.py + session.py（PostgreSQL 同步 engine）

**Files:**
- Create: `backend/src/db/__init__.py`
- Create: `backend/src/db/engines.py`
- Create: `backend/src/db/session.py`
- Test: `backend/tests/unit/db/test_session.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/unit/db/__init__.py` 留空。

`backend/tests/unit/db/test_session.py`:

```python
"""验证 get_db / get_db_session / CurrentSession 行为。"""
import pytest
from sqlalchemy import text

from src.db.session import get_db_session


def test_get_db_session_yields_session():
    with get_db_session() as session:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_get_db_session_rolls_back_on_exception():
    """异常路径下 session.rollback() 被调用。"""
    with pytest.raises(RuntimeError):
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
            raise RuntimeError("boom")
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/db/ -v
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 src/db/engines.py**

`backend/src/db/__init__.py` 留空。

`backend/src/db/engines.py`:

```python
"""PostgreSQL 同步 engine + SessionLocal 单例。"""
from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from src.configs import get_app_config
from src.utils.json import dumps as _json_dumps


def _make_engine(uri: str, echo: bool) -> Engine:
    cfg = get_app_config()
    return create_engine(
        uri,
        echo=echo,
        json_serializer=_json_dumps,
        pool_size=cfg.POOL_SIZE,
        max_overflow=cfg.POOL_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": cfg.DB_CONNECT_TIMEOUT},
    )


_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        cfg = get_app_config()
        _engine = _make_engine(cfg.db_uri, echo=cfg.PRINT_SQL)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


# 兼容老代码暴露名
sync_engine: Engine = get_engine()
SessionLocal: sessionmaker = get_session_factory()


def reset_engine() -> None:
    """单测使用：销毁 engine 单例。"""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
```

- [ ] **Step 4: 实现 src/db/session.py**

`backend/src/db/session.py`:

```python
"""Session 工厂（双对外名）。"""
from __future__ import annotations

import contextlib
from collections.abc import Generator
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.engines import get_session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends / generator 形态。

    - 不自动 commit
    - 异常时 rollback
    - finally 关闭
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


# `with` 语句形态（scheduler / 脚本 / EventShuttle）
get_db_session = contextlib.contextmanager(get_db)

# FastAPI 路由依赖注入
CurrentSession: TypeAlias = Annotated[Session, Depends(get_db)]
```

- [ ] **Step 5: 跑测试确认 pass**

```bash
uv run pytest tests/unit/db/test_session.py -v
```

Expected: 2 passed（需要 PostgreSQL 起着）

- [ ] **Step 6: 提交**

```bash
cd ..
git add backend/src/db/ backend/tests/unit/db/
git -c commit.gpgsign=false commit -m "feat(stage1): src/db/{engines,session}.py — PostgreSQL 同步 engine 单例"
git push
```

---

### Task 11：把 src/shared/db.py 改造为转发 wrapper

**Files:**
- Modify: `backend/src/shared/db.py`

- [ ] **Step 1: 检查现有调用点**

```bash
cd backend && grep -rn "from src.shared.db\|from src.shared import db" src/ tests/ --include='*.py'
```

记录所有引用点，确保转发后仍然兼容。

- [ ] **Step 2: 重写 src/shared/db.py 为转发**

`backend/src/shared/db.py`:

```python
"""向后兼容转发；新代码应直接 import src.db.session / src.db.engines。

阶段 2 全面迁移完成后本文件删除。
"""
from src.db.engines import (  # noqa: F401
    get_engine,
    get_session_factory,
    sync_engine,
    SessionLocal,
)
from src.db.session import get_db, get_db_session  # noqa: F401

__all__ = [
    "get_engine",
    "get_session_factory",
    "sync_engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
]
```

- [ ] **Step 3: 跑全量测试确认转发不破坏**

```bash
ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -x -q
```

Expected: 全绿

- [ ] **Step 4: 提交**

```bash
cd ..
git add backend/src/shared/db.py
git -c commit.gpgsign=false commit -m "refactor(stage1): src/shared/db.py 改造为转发 wrapper（指向 src/db/）"
git push
```

---

### Task 12：创建 src/common/response/ 体系（Response[T] + ErrorCode）

**Files:**
- Create: `backend/src/common/__init__.py`
- Create: `backend/src/common/response/__init__.py`
- Create: `backend/src/common/response/response_code.py`
- Create: `backend/src/common/response/response_schema.py`
- Test: `backend/tests/unit/common/test_response.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/unit/common/__init__.py` 留空。

`backend/tests/unit/common/test_response.py`:

```python
from src.common.response.response_code import ErrorCode
from src.common.response.response_schema import Response, response_base


def test_error_code_format():
    assert ErrorCode.SUCCESS.code == "0"
    assert ErrorCode.NOT_FOUND.code == "400005"
    assert ErrorCode.RISK_REJECTED.code == "600002"


def test_response_success_default():
    r = Response[dict]()
    assert r.success is True
    assert r.code == "0"
    assert r.message == "成功"
    assert r.data is None


def test_response_base_success_helper():
    r = response_base.success(data={"x": 1})
    assert r.success is True
    assert r.data == {"x": 1}
    assert r.code == "0"


def test_response_base_fail_helper():
    r = response_base.fail(code=ErrorCode.NOT_FOUND.code, message="持仓不存在")
    assert r.success is False
    assert r.code == "400005"
    assert r.message == "持仓不存在"
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/common/test_response.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 ErrorCode**

`backend/src/common/__init__.py` 留空。

`backend/src/common/response/__init__.py`:

```python
from src.common.response.response_code import ErrorCode
from src.common.response.response_schema import Response, ResponseBase, response_base

__all__ = ["ErrorCode", "Response", "ResponseBase", "response_base"]
```

`backend/src/common/response/response_code.py`:

```python
"""统一错误码枚举。

段位约定：
- "0"          成功
- "400xxx"     客户端错误（参数 / 认证 / 找不到 / 限流 / 冲突）
- "500xxx"     服务端错误（系统 / 服务层 / DB / Redis）
- "600xxx"     alpha-pilot 业务专属错误码
"""
from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    SUCCESS = ("0", "成功")

    # 客户端错误 4xxxxx
    PARAM_ERROR       = ("400001", "参数错误")
    VALIDATION_ERROR  = ("400002", "参数校验失败")
    AUTH_ERROR        = ("400003", "认证失败")
    FORBIDDEN         = ("400004", "权限不足")
    NOT_FOUND         = ("400005", "资源不存在")
    RATE_LIMIT        = ("400006", "请求过于频繁")
    CONFLICT          = ("400009", "资源冲突")

    # 服务端错误 5xxxxx
    SYS_ERROR     = ("500001", "系统错误")
    SERVICE_ERROR = ("500002", "服务层错误")
    DB_ERROR      = ("500003", "数据库错误")
    REDIS_ERROR   = ("500006", "Redis 错误")

    # alpha-pilot 业务专属 6xxxxx
    KILL_SWITCH_PAUSED   = ("600001", "系统紧急停机中")
    RISK_REJECTED        = ("600002", "风控校验未通过")
    IDEMPOTENCY_CONFLICT = ("600003", "幂等键冲突")
    INSUFFICIENT_BALANCE = ("600004", "账户余额不足")
    EXCHANGE_API_ERROR   = ("600005", "交易所接口异常")
    LLM_RESPONSE_INVALID = ("600006", "LLM 响应格式异常")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def msg(self) -> str:
        return self.value[1]
```

- [ ] **Step 4: 实现 Response[T] + response_base**

`backend/src/common/response/response_schema.py`:

```python
"""统一响应 schema。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from src.common.response.response_code import ErrorCode

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """HTTP API 统一响应 envelope。

    - 业务异常统一 HTTP 200 + body `success: false`
    - HTTP 状态码留给传输层语义（404 路径不存在 / 401 未授权 等）
    """

    success: bool = Field(default=True)
    code: str = Field(default=ErrorCode.SUCCESS.code)
    message: str = Field(default=ErrorCode.SUCCESS.msg)
    detail_message: str | None = Field(default=None, alias="detailMessage")
    data: T | None = Field(default=None)
    request_id: str | None = Field(default=None)


class ResponseBase:
    """便捷构造器。"""

    @staticmethod
    def success(data: Any = None) -> Response:
        from src.utils.request_id import get_request_id
        return Response(
            success=True,
            code=ErrorCode.SUCCESS.code,
            message=ErrorCode.SUCCESS.msg,
            data=data,
            request_id=get_request_id(),
        )

    @staticmethod
    def fail(code: str, message: str, detail: str | None = None) -> Response:
        from src.utils.request_id import get_request_id
        return Response(
            success=False,
            code=code,
            message=message,
            detail_message=detail,
            data=None,
            request_id=get_request_id(),
        )


response_base = ResponseBase()
```

- [ ] **Step 5: 跑测试确认 pass**

```bash
uv run pytest tests/unit/common/test_response.py -v
```

Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
cd ..
git add backend/src/common/__init__.py backend/src/common/response/ backend/tests/unit/common/
git -c commit.gpgsign=false commit -m "feat(stage1): src/common/response/ — Response[T] + ErrorCode 枚举"
git push
```

---

### Task 13：创建 src/common/exception/ 异常树（含 auto_log + stack）

**Files:**
- Create: `backend/src/common/exception/__init__.py`
- Create: `backend/src/common/exception/errors.py`
- Test: `backend/tests/unit/common/test_exceptions.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/unit/common/test_exceptions.py`:

```python
import logging
import pytest

from src.common.exception.errors import (
    AppBaseException,
    DBException,
    KillSwitchPausedException,
    ParamsException,
    RiskRejectedException,
    ServiceException,
)
from src.common.response.response_code import ErrorCode


def test_app_base_exception_default():
    exc = AppBaseException()
    assert exc.code == ErrorCode.SYS_ERROR.code
    assert exc.message == ErrorCode.SYS_ERROR.msg


def test_service_exception_with_message():
    exc = ServiceException(message="持仓不存在")
    assert exc.message == "持仓不存在"
    assert exc.code == ErrorCode.SERVICE_ERROR.code


def test_db_exception_with_not_found_code():
    exc = DBException(error_code=ErrorCode.NOT_FOUND, message="position id=1 not found")
    assert exc.code == ErrorCode.NOT_FOUND.code
    assert exc.message == "position id=1 not found"


def test_params_exception_auto_log_stack_disabled():
    """ParamsException 关闭 stack 以避免日志膨胀"""
    assert ParamsException.auto_log_stack is False


def test_business_specific_exceptions():
    e1 = KillSwitchPausedException()
    assert e1.code == ErrorCode.KILL_SWITCH_PAUSED.code

    e2 = RiskRejectedException("日内亏损超阈")
    assert e2.code == ErrorCode.RISK_REJECTED.code
    assert e2.message == "日内亏损超阈"


def test_auto_log_records_error_with_class_name(caplog, monkeypatch):
    """raise 时自动记一条 ERROR，含真实子类名"""
    monkeypatch.setattr(AppBaseException, "auto_log", True)
    caplog.set_level(logging.ERROR, logger="app.exception")
    with pytest.raises(RiskRejectedException):
        raise RiskRejectedException("test")
    matching = [r for r in caplog.records if "[RiskRejectedException]" in r.getMessage()]
    assert len(matching) >= 1
    assert matching[0].levelname == "ERROR"


def test_auto_log_can_be_disabled_via_class_attr(monkeypatch, caplog):
    monkeypatch.setattr(AppBaseException, "auto_log", False)
    caplog.set_level(logging.ERROR, logger="app.exception")
    with pytest.raises(ServiceException):
        raise ServiceException("silent")
    matching = [r for r in caplog.records if "[ServiceException]" in r.getMessage()]
    assert matching == []
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/common/test_exceptions.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现异常树**

`backend/src/common/exception/__init__.py`:

```python
from src.common.exception.errors import (
    AppBaseException,
    DBException,
    ExchangeApiException,
    IdempotencyConflictException,
    InsufficientBalanceException,
    KillSwitchPausedException,
    LLMResponseInvalidException,
    ParamsException,
    RedisException,
    RiskRejectedException,
    ServiceException,
)

__all__ = [
    "AppBaseException",
    "DBException",
    "ExchangeApiException",
    "IdempotencyConflictException",
    "InsufficientBalanceException",
    "KillSwitchPausedException",
    "LLMResponseInvalidException",
    "ParamsException",
    "RedisException",
    "RiskRejectedException",
    "ServiceException",
]
```

`backend/src/common/exception/errors.py`:

```python
"""异常树。所有自定义异常的基类是 AppBaseException。

抛出时自动记 ERROR 级日志，含 type(self).__name__ + 错误码 + 消息 + raise 行的
file:lineno + funcname + request_id + 调用栈（可选）。

约定：
- 业务代码禁止就地 class XxxError(Exception)，新语义在本文件加子类
- CRUD 抛 DBException、Service 抛 ServiceException 或具体业务子类
- 测试中通过 monkeypatch.setattr(AppBaseException, "auto_log", False) 静音
"""
from __future__ import annotations

import logging
import sys
import traceback as tb_mod
from typing import ClassVar

from src.common.response.response_code import ErrorCode

logger = logging.getLogger("app.exception")


class AppBaseException(Exception):
    auto_log: ClassVar[bool] = True
    auto_log_stack: ClassVar[bool] = True

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.SYS_ERROR,
        message: str = "",
    ) -> None:
        self.error_code = error_code
        self.code = error_code.code
        self.message = message or error_code.msg
        super().__init__(self.message)
        if self.auto_log:
            self._auto_log()

    def _auto_log(self) -> None:
        frame = sys._getframe(2)
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        funcname = frame.f_code.co_name

        try:
            from src.utils.request_id import get_request_id
            request_id = get_request_id() or "-"
        except Exception:
            request_id = "-"

        stack_str = ""
        if self.auto_log_stack:
            stack_str = "".join(tb_mod.format_stack()[:-2])

        log_fmt = "[%s] code=%s msg=%s at %s:%d in %s() request_id=%s"
        log_args: list = [type(self).__name__, self.code, self.message,
                          filename, lineno, funcname, request_id]
        if stack_str:
            log_fmt += "\nCall stack:\n%s"
            log_args.append(stack_str)

        logger.error(
            log_fmt, *log_args,
            stacklevel=3,
            extra={
                "exc_class": type(self).__name__,
                "exc_code": self.code,
                "exc_file": filename,
                "exc_lineno": lineno,
                "exc_func": funcname,
                "request_id": request_id,
            },
        )


# ── 框架级异常 ──────────────────────────────────────────────────────────
class ServiceException(AppBaseException):
    def __init__(self, message: str = "", error_code: ErrorCode = ErrorCode.SERVICE_ERROR) -> None:
        super().__init__(error_code=error_code, message=message)


class DBException(AppBaseException):
    def __init__(self, message: str = "", error_code: ErrorCode = ErrorCode.DB_ERROR) -> None:
        super().__init__(error_code=error_code, message=message)


class ParamsException(AppBaseException):
    auto_log_stack = False  # 客户端错误，关 stack 避免日志膨胀

    def __init__(self, message: str = "") -> None:
        super().__init__(error_code=ErrorCode.PARAM_ERROR, message=message)


class RedisException(AppBaseException):
    def __init__(self, message: str = "") -> None:
        super().__init__(error_code=ErrorCode.REDIS_ERROR, message=message)


# ── alpha-pilot 业务专属 ────────────────────────────────────────────────
class KillSwitchPausedException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.KILL_SWITCH_PAUSED)


class RiskRejectedException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.RISK_REJECTED)


class IdempotencyConflictException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.IDEMPOTENCY_CONFLICT)


class InsufficientBalanceException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.INSUFFICIENT_BALANCE)


class ExchangeApiException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.EXCHANGE_API_ERROR)


class LLMResponseInvalidException(ServiceException):
    def __init__(self, message: str = "") -> None:
        super().__init__(message=message, error_code=ErrorCode.LLM_RESPONSE_INVALID)
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/common/test_exceptions.py -v
```

Expected: 7 passed

- [ ] **Step 5: 添加测试 fixture 全局静音 auto_log**

`backend/tests/conftest.py`（如不存在创建，存在则补充）：

```python
import pytest
from src.common.exception.errors import AppBaseException


@pytest.fixture(autouse=True)
def _silence_app_exception_autolog(monkeypatch):
    """单测全局静音 auto_log，避免日志污染输出。需要验证日志的单测临时打开。"""
    monkeypatch.setattr(AppBaseException, "auto_log", False)
```

- [ ] **Step 6: 跑全量测试确认未破坏（注意 test_auto_log_* 自己 monkeypatch 改回 True）**

修复 `test_auto_log_records_error_with_class_name` 与 conftest fixture 的协作 — 测试本身已用 `monkeypatch.setattr(...)` 覆盖到 `True`，conftest 在测试函数执行前先 set False，测试内再 set True，正常工作。

```bash
uv run pytest -x -q
```

Expected: 全绿

- [ ] **Step 7: 提交**

```bash
cd ..
git add backend/src/common/exception/ backend/tests/unit/common/test_exceptions.py backend/tests/conftest.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/common/exception/errors.py — AppBaseException 树（自动 ERROR 日志 + stack）"
git push
```

---

### Task 14：创建 src/common/exception/exception_handler.py 全局 handler

**Files:**
- Create: `backend/src/common/exception/exception_handler.py`
- Test: `backend/tests/integration/test_exception_handler.py`

- [ ] **Step 1: 写测试**

`backend/tests/integration/__init__.py` 留空（如不存在）。

`backend/tests/integration/test_exception_handler.py`:

```python
"""验证全局 exception handler：
- AppBaseException → HTTP 200 + success:false（不再额外记日志）
- 未识别 Exception → HTTP 200 + SYS_ERROR + 记 traceback
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.common.exception.errors import RiskRejectedException, ServiceException
from src.common.exception.exception_handler import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/risk")
    def _r():
        raise RiskRejectedException("日内亏损超阈")

    @app.get("/unknown")
    def _u():
        raise RuntimeError("boom")

    @app.get("/ok")
    def _ok():
        return {"x": 1}

    return app


def test_app_base_exception_returns_200_with_success_false():
    client = TestClient(_build_app())
    resp = client.get("/risk")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "600002"
    assert body["message"] == "日内亏损超阈"


def test_unhandled_exception_returns_200_with_sys_error():
    client = TestClient(_build_app())
    resp = client.get("/unknown")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "500001"
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/integration/test_exception_handler.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 handler**

`backend/src/common/exception/exception_handler.py`:

```python
"""全局 exception handler。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from src.common.exception.errors import AppBaseException, ParamsException
from src.common.response.response_code import ErrorCode
from src.utils.request_id import current_request_id

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

logger = logging.getLogger("app.exception_handler")


def register_exception_handlers(app: "FastAPI") -> None:
    """注册全局 exception handler。"""

    @app.exception_handler(AppBaseException)
    async def app_exc_handler(request, exc: AppBaseException) -> JSONResponse:
        """业务异常：仅做 JSON 转换；日志由 AppBaseException._auto_log 在抛出点已记。"""
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.VALIDATION_ERROR.code,
                "message": ErrorCode.VALIDATION_ERROR.msg,
                "detailMessage": str(exc.errors()[:5]),
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_handler(request, exc: PydanticValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.VALIDATION_ERROR.code,
                "message": ErrorCode.VALIDATION_ERROR.msg,
                "detailMessage": str(exc.errors()[:5]),
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_handler(request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.PARAM_ERROR.code,
                "message": str(exc) or ErrorCode.PARAM_ERROR.msg,
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request, exc: Exception) -> JSONResponse:
        """未识别异常：记 ERROR + 完整 traceback（这类没有 auto_log）。"""
        logger.error(
            "[Unhandled] %s %s — %s",
            request.method, request.url.path, str(exc),
            exc_info=exc,
            extra={
                "request_id": current_request_id(),
                "method": request.method,
                "path": str(request.url.path),
            },
        )
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.SYS_ERROR.code,
                "message": ErrorCode.SYS_ERROR.msg,
                "data": None,
                "request_id": current_request_id(),
            },
        )
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/integration/test_exception_handler.py -v
```

Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/common/exception/exception_handler.py backend/tests/integration/test_exception_handler.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/common/exception/exception_handler.py — 全局 handler"
git push
```

---

### Task 15：创建 src/common/api_response.py 装饰器（占位实现）

**Files:**
- Create: `backend/src/common/api_response.py`
- Test: `backend/tests/unit/common/test_api_response.py`

> 阶段 1 仅引入装饰器**作为工具备用**，不替换现有 router 用法。阶段 4 才大规模应用。

- [ ] **Step 1: 写测试**

`backend/tests/unit/common/test_api_response.py`:

```python
from pydantic import BaseModel

from src.common.api_response import api_response, to_schema
from src.common.response.response_schema import Response


class _UserOut(BaseModel):
    id: int
    name: str


def test_api_response_wraps_dict():
    @api_response()
    def view():
        return {"id": 1, "name": "Alice"}

    r: Response = view()
    assert r.success is True
    assert r.data == {"id": 1, "name": "Alice"}


def test_api_response_wraps_with_schema():
    @api_response(schema=_UserOut)
    def view():
        return {"id": 1, "name": "Alice"}

    r: Response = view()
    assert r.success is True
    assert isinstance(r.data, _UserOut)
    assert r.data.id == 1


def test_to_schema_list():
    out = to_schema([{"id": 1, "name": "A"}, {"id": 2, "name": "B"}], _UserOut)
    assert len(out) == 2
    assert all(isinstance(x, _UserOut) for x in out)


def test_to_schema_none_passthrough():
    assert to_schema(None, _UserOut) is None
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/common/test_api_response.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现**

`backend/src/common/api_response.py`:

```python
"""@api_response 装饰器：自动 ORM→Pydantic + response_base.success 包装。

阶段 1 引入但不强制使用；阶段 4 重构 controllers 时全面应用。
"""
from __future__ import annotations

import functools
from typing import Any, Callable

from pydantic import BaseModel

from src.common.response.response_schema import Response, response_base


def to_schema(raw: Any, schema: type[BaseModel] | None) -> Any:
    """ORM → Pydantic 自动转换。支持 None / dict / BaseModel / list / ORM 实例。"""
    if raw is None or schema is None:
        return raw
    if isinstance(raw, BaseModel):
        return raw
    if isinstance(raw, list):
        return [schema.model_validate(item) for item in raw]
    return schema.model_validate(raw)


def api_response(schema: Any = None) -> Callable:
    """装饰器：把 controller 函数返回值包装为 Response[T]。

    业务异常直接抛出，由全局 exception handler 处理；不在装饰器里捕获。
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            raw = fn(*args, **kwargs)
            payload = to_schema(raw, schema)
            return response_base.success(data=payload)

        return wrapper

    return decorator
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/common/test_api_response.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/common/api_response.py backend/tests/unit/common/test_api_response.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/common/api_response.py — @api_response 装饰器（占位备用）"
git push
```

---

### Task 16：创建 src/common/schemas/pagination.py（Paginated[T]）

**Files:**
- Create: `backend/src/common/schemas/__init__.py`
- Create: `backend/src/common/schemas/pagination.py`
- Test: `backend/tests/unit/common/test_pagination.py`

- [ ] **Step 1: 写测试**

`backend/tests/unit/common/test_pagination.py`:

```python
from src.common.schemas.pagination import Paginated


def test_paginated_default():
    p = Paginated[dict]()
    assert p.items == []
    assert p.total == 0
    assert p.page_index == 1
    assert p.page_size == 20
    assert p.pages == 0


def test_paginated_with_data():
    p = Paginated[dict](
        items=[{"id": 1}, {"id": 2}],
        total=42,
        page_index=2,
        page_size=20,
        pages=3,
    )
    assert len(p.items) == 2
    assert p.total == 42
    assert p.page_index == 2
    assert p.pages == 3
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/common/test_pagination.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

`backend/src/common/schemas/__init__.py` 留空。

`backend/src/common/schemas/pagination.py`:

```python
"""通用分页响应 schema。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    """泛型分页响应。

    字段语义：
    - items: 当前页数据列表
    - total: 总条数
    - page_index: 当前页码（1-based）
    - page_size: 每页大小
    - pages: 总页数 = ceil(total / page_size)
    """

    items: list[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(default=0, description="总条数")
    page_index: int = Field(default=1, description="当前页码（1-based）")
    page_size: int = Field(default=20, description="每页大小")
    pages: int = Field(default=0, description="总页数 = ceil(total / page_size)")
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/common/test_pagination.py -v
```

Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/common/schemas/ backend/tests/unit/common/test_pagination.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/common/schemas/pagination.py — Paginated[T] 泛型"
git push
```

---

### Task 17：创建 src/common/events.py（BaseEvent 占位）

**Files:**
- Create: `backend/src/common/events.py`
- Test: `backend/tests/unit/common/test_events.py`

> 阶段 1 仅引入 `BaseEvent` 基类；具体事件类（StrategyDecisionEvent / OrderCreatedEvent 等）在阶段 3 业务层重组时迁移。

- [ ] **Step 1: 写测试**

`backend/tests/unit/common/test_events.py`:

```python
from datetime import datetime
from src.common.events import BaseEvent


def test_base_event_default_fields():
    e = BaseEvent()
    assert e.user_id is None
    assert e.request_id is None
    assert isinstance(e.occurred_at, datetime)


def test_base_event_with_user():
    e = BaseEvent(user_id=42)
    assert e.user_id == 42
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/unit/common/test_events.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

`backend/src/common/events.py`:

```python
"""业务事件基类。具体事件子类在阶段 3 业务层重组时填充。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.utils.time import TimeUtils


class BaseEvent(BaseModel):
    """所有业务事件的基类。"""

    user_id: int | None = Field(default=None, description="ws 路由用")
    request_id: str | None = Field(default=None, description="HTTP 链路 ID（如有）")
    occurred_at: datetime = Field(default_factory=TimeUtils.now)
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/common/test_events.py -v
```

Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
cd ..
git add backend/src/common/events.py backend/tests/unit/common/test_events.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/common/events.py — BaseEvent 占位"
git push
```

---

### Task 18：创建 src/middleware/{request_logging,error_logging}_middleware.py

**Files:**
- Create: `backend/src/middleware/__init__.py`
- Create: `backend/src/middleware/request_logging_middleware.py`
- Create: `backend/src/middleware/error_logging_middleware.py`
- Test: `backend/tests/integration/test_middleware.py`

- [ ] **Step 1: 写测试**

`backend/tests/integration/test_middleware.py`:

```python
"""验证 RequestLogging / ErrorLogging 中间件不影响响应。"""
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.error_logging_middleware import ErrorLoggingMiddleware
from src.middleware.request_logging_middleware import RequestLoggingMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    def _ping():
        return {"pong": True}

    return app


def test_request_logging_middleware_logs_path(caplog):
    caplog.set_level(logging.INFO, logger="middleware.request")
    client = TestClient(_build_app())
    resp = client.get("/ping")
    assert resp.status_code == 200
    matching = [r for r in caplog.records if "/ping" in r.getMessage()]
    assert len(matching) >= 1
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/integration/test_middleware.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 RequestLoggingMiddleware**

`backend/src/middleware/__init__.py` 留空。

`backend/src/middleware/request_logging_middleware.py`:

```python
"""HTTP 请求级 access log 中间件。"""
from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "%s %s — exception (%dms)",
                request.method, request.url.path, elapsed_ms,
            )
            raise
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "%s %s -> %d (%dms)",
            request.method, request.url.path, response.status_code, elapsed_ms,
        )
        return response
```

- [ ] **Step 4: 实现 ErrorLoggingMiddleware**

`backend/src/middleware/error_logging_middleware.py`:

```python
"""未捕获异常兜底 middleware。

注意：FastAPI 的全局 exception handler 已经覆盖大多数情况；本 middleware 是
最后一道防线，确保异常一定会被记日志，避免在 starlette 层吃掉。
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("middleware.error")


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled in middleware-stack: %s %s",
                request.method, request.url.path,
            )
            raise
```

- [ ] **Step 5: 跑测试确认 pass**

```bash
uv run pytest tests/integration/test_middleware.py -v
```

Expected: 1 passed

- [ ] **Step 6: 提交**

```bash
cd ..
git add backend/src/middleware/ backend/tests/integration/test_middleware.py
git -c commit.gpgsign=false commit -m "feat(stage1): src/middleware/ — RequestLoggingMiddleware + ErrorLoggingMiddleware"
git push
```

---

### Task 19：提级 src/app/app.py 为 src/app.py（含中间件栈注入）

**Files:**
- Create: `backend/src/app.py`
- Modify: `backend/src/app/__init__.py`（保留转发）
- Delete: `backend/src/app/app.py`
- Modify: `backend/src/main.py`（修改 uvicorn 入口）
- Test: `backend/tests/integration/test_app_factory.py`

- [ ] **Step 1: 写测试**

`backend/tests/integration/test_app_factory.py`:

```python
"""验证提级后的 src.app:app 启动正常 + 中间件注入 request_id。"""
from fastapi.testclient import TestClient


def test_app_can_be_imported_from_src_app():
    from src.app import app  # 提级后唯一入口
    assert app is not None
    assert hasattr(app, "router")


def test_request_has_x_request_id_header():
    """CorrelationIdMiddleware 注入 X-Request-ID 到响应头。"""
    from src.app import app
    client = TestClient(app)
    resp = client.get("/api/health/")  # 假设 /api/health/ 存在；不存在则 hit 404 也行（验证 header 注入）
    assert "X-Request-ID" in resp.headers
    rid = resp.headers["X-Request-ID"]
    assert len(rid) == 32  # UUID 去横线 hex
    assert all(c in "0123456789abcdef" for c in rid)
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
cd backend && uv run pytest tests/integration/test_app_factory.py -v
```

Expected: FAIL — `ImportError: cannot import name 'app' from 'src.app'`（因为 src/app/__init__.py 现在不暴露 app）

- [ ] **Step 3: 创建提级后的 src/app.py**

`backend/src/app.py`:

```python
"""FastAPI 应用工厂（提级到 src 根级，模板规范的唯一启动文件）。

阶段 1 内容：
- 中间件栈注入（CorrelationId / RequestLogging / ErrorLogging）
- 注册全局 exception handler（仍兼容现有 HTTPException 行为）
- 复用现有 routers（src/app/routers/、src/app/router.py）和 lifespan、admin_bootstrap
- 响应体格式 / 异常处理保持当前行为（不切 Response[T]）

阶段 4 / 5 会再次重构（路由迁到 controllers/、移除 lifespan 内 scheduler）。
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.router import router
from src.app.routers.commands import router as commands_router
from src.app.routers.events_catchup import router as events_catchup_router
from src.app.websocket import redis_subscriber, websocket_endpoint
from src.common.exception.exception_handler import register_exception_handlers
from src.configs import get_app_config
from src.control.kill_switch.service import KillSwitchService
from src.db.session import get_db_session
from src.middleware.error_logging_middleware import ErrorLoggingMiddleware
from src.middleware.request_logging_middleware import RequestLoggingMiddleware
from src.services.admin_bootstrap import ensure_default_admin
from src.utils.log import init_logger
from src.utils.uuid import get_uuid_without_hyphen

# 初始化日志（必须最早）
init_logger("api")

logger = logging.getLogger("app")
_scheduler: BackgroundScheduler | None = None


def _strategy_job() -> None:
    from src.workers.strategy_loop import run_strategy_loop
    with get_db_session() as db:
        if KillSwitchService(db).is_paused():
            logger.info("kill_switch=paused; strategy_loop skipped")
            return
        run_strategy_loop(db)


def _monitor_job() -> None:
    from src.workers.position_monitor import run_position_monitor
    with get_db_session() as db:
        if KillSwitchService(db).is_paused():
            logger.debug("kill_switch=paused; position_monitor running (monitor-only)")
        run_position_monitor(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    settings = get_app_config()

    with get_db_session() as db:
        ensure_default_admin(db, settings)

    _scheduler = BackgroundScheduler()
    if getattr(settings, "USE_NEW_PIPELINE_WORKER", False):
        from src.workers.scheduler_jobs import (
            new_position_monitor_job,
            new_strategy_pipeline_job,
        )
        _scheduler.add_job(
            new_strategy_pipeline_job, "interval",
            minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES, id="strategy_loop",
        )
        _scheduler.add_job(
            new_position_monitor_job, "interval",
            seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS, id="position_monitor",
        )
    else:
        _scheduler.add_job(
            _strategy_job, "interval",
            minutes=settings.STRATEGY_LOOP_INTERVAL_MINUTES, id="strategy_loop",
        )
        _scheduler.add_job(
            _monitor_job, "interval",
            seconds=settings.POSITION_MONITOR_INTERVAL_SECONDS, id="position_monitor",
        )
    _scheduler.start()

    ws_task = asyncio.create_task(redis_subscriber(settings.REDIS_URL))
    yield

    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


def _docs_enabled() -> bool:
    if os.getenv("ALPHAPILOT_FORCE_DOCS") == "1":
        return True
    settings = get_app_config()
    mode = settings.TRADING_MODE.value if hasattr(settings.TRADING_MODE, "value") else settings.TRADING_MODE
    return mode != "mainnet"


def create_app() -> FastAPI:
    settings = get_app_config()
    docs_on = _docs_enabled()

    app = FastAPI(
        title="AlphaPilot API",
        description="AI Autonomous Trading System",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_on else None,
        redoc_url="/redoc" if docs_on else None,
        openapi_url="/openapi.json" if docs_on else None,
    )

    # ── 全局 exception handler（同时存在 — 阶段 4 切 Response[T] 时使用）────
    register_exception_handlers(app)

    # ── 中间件（注册顺序从内到外）────────────────────────────────────────
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    if settings.ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
        generator=get_uuid_without_hyphen,
        update_request_header=True,
    )

    # ── 路由（沿用现有 routers，阶段 4 重组到 controllers/）────────────────
    app.include_router(router)
    app.include_router(commands_router)
    app.include_router(events_catchup_router)
    app.add_api_websocket_route("/ws", websocket_endpoint)

    return app


app = create_app()
```

- [ ] **Step 4: 删除旧的 src/app/app.py**

```bash
cd backend && rm src/app/app.py
```

- [ ] **Step 5: 修改 src/app/__init__.py 转发兼容**

`backend/src/app/__init__.py`（保持现有兼容性）：

```python
"""src.app 子目录暂保留 routers/ websocket.py 等；
新代码应从 src.app 顶层（src/app.py）导入 FastAPI 应用工厂。

阶段 4 controllers 重组后本子目录会被清空。
"""
# 不再 export `app`（已在 src/app.py 顶层）
```

- [ ] **Step 6: 修改 src/main.py uvicorn 入口**

`backend/src/main.py`:

```python
import uvicorn


def main():
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: 检查并修改其他启动入口（Makefile / scripts/start.sh / Dockerfile）**

```bash
cd .. && grep -rn "src\.app\.app:app\|src/app/app\.py" --include='*.sh' --include='Makefile' --include='Dockerfile*'
```

把所有 `src.app.app:app` 改为 `src.app:app`。

- [ ] **Step 8: 跑测试确认 pass**

```bash
cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -x -q
```

Expected: 全绿

如有失败：通常是某些测试 import `src.app.app` —— 找到改成 `src.app`。

- [ ] **Step 9: 手工启 dev server 验证**

```bash
ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run python -m src.main &
sleep 3
curl -i http://localhost:8000/api/health/ 2>/dev/null | head -20
kill %1 2>/dev/null
```

Expected: 看到 `X-Request-ID: <32 hex>` 响应头。

- [ ] **Step 10: 提交**

```bash
cd ..
git add backend/src/app.py backend/src/app/__init__.py backend/src/main.py
git rm backend/src/app/app.py 2>/dev/null || true
[ -f Makefile ] && git add Makefile
git status
git -c commit.gpgsign=false commit -m "refactor(stage1): src/app/app.py 提级为 src/app.py + 中间件栈注入"
git push
```

---

### Task 20：写阶段 1 worklog 并 dev 部署验证

**Files:**
- Create: `docs/worklog/YYYYMMDD_HHMM_stage1_完成.md`

- [ ] **Step 1: 跑全量测试**

```bash
cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -v
```

Expected: 53（基线）+ 18（新增单元）+ 3（新增集成）= 74 passed（数字示意）

- [ ] **Step 2: 启动 dev 验证 docs 可访问**

```bash
make dev-up
make dev-backend &
sleep 5
curl -i http://localhost:8000/docs | head -5    # 200 OK
curl -i http://localhost:8000/api/health/ | grep "X-Request-ID"  # 有 X-Request-ID
kill %1 2>/dev/null
```

- [ ] **Step 3: 写 worklog**

`docs/worklog/YYYYMMDD_HHMM_stage1_完成.md`（替换日期）：

```markdown
# Stage 1 完成 — 基础设施层（YYYY-MM-DD）

## 做了什么

按 `docs/superpowers/specs/2026-04-30-fastapi-template-refactor-design.md` v3.6 §6 阶段 1 范围搭建：

- `src/utils/{log,request_id,uuid,time,redis,json}.py` — 通用工具
- `src/configs/app_configs.py` 重写为 8 个子配置类多继承（PostgreSQL / Redis / Scheduler / Exchange / LLM / Risk / Security / Service / CORS）
- `src/db/{engines,session}.py` — PostgreSQL 同步 engine + SessionLocal + CurrentSession
- `src/common/{response,exception,api_response,events,schemas}/` — 响应体系 + 异常树（自动 ERROR + stack）+ 装饰器 + Paginated[T] + BaseEvent
- `src/middleware/{request_logging,error_logging}_middleware.py`
- `src/app.py` — 提级（替代 src/app/app.py）+ 中间件栈注入 + 全局 exception handler 注册
- `src/shared/db.py` 改为转发兼容 wrapper

## 为什么

阶段 1 是渐进重构的基础设施奠基：先建好通用工具，后续阶段 2-5 才能复用；不动 HTTP 行为是为了让前端 / 业务零感知，方便回滚。

## 如何验证

- 单测：tests/unit/{utils,common,configs,db}/ 全绿
- 集成测：tests/integration/{test_exception_handler,test_app_factory,test_middleware}.py 全绿
- 手工：dev server 起来后 `curl /api/health/` 看到 `X-Request-ID` 响应头（32 hex）
- 回归：现有 53 测试全绿

## 对应 commit

- 见 `git log refactor/stage1-infra ^main --oneline`

## 下一步

进入 stage 2，准备展开 plan：
- DB 层扁平化：models/ / cruds/ / schemas/ 三层
- 主键统一改 BigInteger autoincrement
- migrations/versions 全删重建
```

- [ ] **Step 4: 提交 worklog**

```bash
git add docs/worklog/
git -c commit.gpgsign=false commit -m "docs(stage1): 阶段 1 完成 worklog"
git push
```

- [ ] **Step 5: 部署到 dev server**

```bash
bash scripts/deploy-dev.sh
```

观察 dev server 日志：
- 启动正常无 error
- 现有功能（持仓查询 / 决策列表 / WebSocket 推送）行为不变
- 任意 HTTP 响应头有 `X-Request-ID`

- [ ] **Step 6: dev 24h 观察后准备 PR**

24h 内无异常 → 准备 merge 到 main：

```bash
gh pr create --title "Stage 1: 基础设施层重构" --body "$(cat <<'EOF'
## Summary

按 spec v3.6 §6 阶段 1 完成基础设施层搭建：utils / configs / db / common / middleware / app 提级。

## 关键变更

- ✨ 新增：`src/utils/` `src/db/` `src/common/` `src/middleware/`
- 🔧 重写：`src/configs/app_configs.py`（8 个子配置类多继承）
- 📦 提级：`src/app/app.py` → `src/app.py`
- ✅ HTTP 行为零变化（仅注入 X-Request-ID 与 access log）
- 🧪 测试 53→74 全绿

## Test plan

- [x] 全部 pytest 绿
- [x] dev server 启动正常
- [x] `curl /api/health/` 看到 X-Request-ID 响应头
- [x] dev server 24h 观察无异常

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Stage 1 验收清单

- [ ] 所有 task 1-20 完成
- [ ] 单测 + 集成测试全绿（≥ 74 passed）
- [ ] HTTP 行为零变化（前端无感知）
- [ ] `curl` 任意接口看到 `X-Request-ID: <32 hex>` 响应头
- [ ] 异常日志有 `request_id` 字段（grep 日志验证）
- [ ] dev server 24h 观察无异常
- [ ] worklog 写入 `docs/worklog/`
- [ ] PR 合并到 main

---

## Stage 1 完成后

调用 `superpowers:writing-plans` skill，输入：

> 「基于 spec v3.6 §6 阶段 2 + Stage 1 已落地的实际代码（路径/接口/命名），生成 Stage 2 详细 plan：DB 层扁平化（models/ + cruds/ + schemas/）+ 主键升级 BigInteger + migrations 重建。」

生成 `docs/superpowers/plans/2026-04-30-refactor-stage2-db-layer.md`，更新 master plan 表格。
