# 20260501 1939 — 修复 test_runtime_config skip

## 做了什么

- 摘掉 `backend/tests/unit/test_runtime_config.py::test_refresh_applies_active_mode_credentials_and_risk_overrides` 的 `@pytest.mark.skip`。
- 未改任何业务代码（`src/shared/runtime_config.py`、`src/core/exchange/binance_client.py` 不动）。

## 为什么

原 skip reason 标注 "apply_runtime_settings_refresh 在测试环境 hang（疑似 binance_client cache 导致）"。
检查链路：`apply_runtime_settings_refresh` 末尾仅调用 `get_binance_client.cache_clear()`，本身不实例化 Client、不发网络请求；`refresh_from_db` 是纯 SQLAlchemy 查询。
直接跑测试 1.91s 通过 —— 历史 hang 推测是早期版本（可能调用过 `get_binance_client()` 实例化）遗留，后续重构已经把 Client 构造移出该函数，skip 标记成了陈旧债务。

## 如何验证

```
cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest \
  tests/unit/test_runtime_config.py::test_refresh_applies_active_mode_credentials_and_risk_overrides -v
# => 1 passed in 1.91s

cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run pytest -q --tb=short
# => 439 passed, 2 skipped, 10 warnings in 63.58s
```

相比修复前（438 passed + 3 skipped），新增 1 passed，少 1 skipped，无回归。

## 对应 commit

见同分支 `fix/runtime-config-deadlock` 头部 commit。
