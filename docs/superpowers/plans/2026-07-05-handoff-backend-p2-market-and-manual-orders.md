# Handoff 后端 P2 — 行情 REST + 手动下单 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 handoff/03 §3.1 行情域三个 REST 接口 + §3.2 手动下单三接口（守卫预检 / 下单 / 改 SL/TP），预检与实际下单同一套守卫规则。

**Architecture:** 交易链路维持现货做多不变；行情页的资金费率/OI/标记价走 Binance USDT-M **公共**行情端点（无密钥，失败返 null）。守卫重构为 `evaluate()` 逐项产出 + `check()` 在其上重建（同一实现保证预检/实盘判定等价）。手动单与 AI 单共用 OrderExecutor 执行内核，幂等 trace_id = SHA256(`manual:{user_id}:{client_order_id}`)[:32]。盘口/逐笔 WS 代理拆到 P2b。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.x 同步 / python-binance / pytest

**权限口径:** 手动下单/改 SL/TP 暂定 `require_admin`（当前仅 user/admin 两角色；P4 RBAC 落地后放宽为 trader+，在 controller 注释注明）。LIMIT 单本期返回业务错误"暂不支持"（V0.1 执行内核为市价 + 监控式 SL/TP），API 字段先收下保证前端契约。

**验收（roadmap P2 后端部分）:** 预检与实际下单判定一致（等价性测试）；HALTED 时非 reduce-only 被拒；`make test` 全绿；ruff 全绿。

---

### Task 1: 交易所类型与适配层扩展（Ticker24h / FuturesMetrics）

**Files:**
- Modify: `backend/src/core/exchange/types.py`（加 `Ticker24h`、`FuturesMetrics`）
- Modify: `backend/src/core/exchange/adapter.py`（加**非抽象**默认方法，返回 None，不破坏既有 stub）
- Modify: `backend/src/core/exchange/binance_adapter.py`（实现两方法）
- Test: `backend/tests/unit/execution/test_binance_adapter_market.py`（新建，mock client）

**契约:**

```python
class Ticker24h(BaseModel):
    symbol: str
    last_price: float
    price_change_pct: float      # 24h 涨跌幅（-0.05 = -5%）
    high_24h: float
    low_24h: float
    volume_24h: float            # base asset 量
    quote_volume_24h: float      # USDT 量

class FuturesMetrics(BaseModel):
    symbol: str
    mark_price: float | None = None
    index_price: float | None = None
    funding_rate: float | None = None
    next_funding_time: datetime | None = None
    open_interest: float | None = None
```

adapter.py（非抽象，默认 None——行情装饰数据非必须）:

```python
    def get_ticker_24h(self, symbol: str) -> "Ticker24h | None":
        return None

    def get_futures_metrics(self, symbol: str) -> "FuturesMetrics | None":
        return None
```

binance_adapter：`get_ticker_24h` 用 spot `client.get_ticker(symbol=...)`（priceChangePercent/highPrice/lowPrice/volume/quoteVolume/lastPrice）；`get_futures_metrics` 用 `client.futures_mark_price(symbol=...)`（markPrice/indexPrice/lastFundingRate/nextFundingTime）+ `client.futures_open_interest(symbol=...)`——**任何异常吞掉记 warning 返 None**（USDT-M 公共数据装饰性，testnet 可能不可用）。两方法走既有 rate_limiter。

**Steps:** 红灯（mock client 返回样例 dict 断言字段映射 + futures 异常时返 None）→ 实现 → 绿灯 → `git commit -m "feat(exchange): 适配层补 24h ticker 与 USDT-M 公共行情指标"` + push。

---

### Task 2: MarketQueryService + GET /api/market/klines

**Files:**
- Create: `backend/src/services/execution/market_query.py`
- Create: `backend/src/controllers/api/v1/market/__init__.py`、`backend/src/controllers/api/v1/market/market.py`
- Modify: `backend/src/controllers/router.py`（注册 market router）
- Modify: `backend/src/cruds/candle_crud.py`（加 `find_latest(session, *, trading_mode, symbol, timeframe, limit)`）
- Test: `backend/tests/unit/execution/test_market_query.py` + `backend/tests/api/test_market_endpoints.py`

**契约:** `GET /api/market/klines?symbol=BTCUSDT&interval=1h&limit=200`（interval 白名单 `1m 5m 15m 1h 4h 1d`，limit 1–1000）→ `[{open_time, open, high, low, close, volume}]`（时间正序）。

**取数策略:** DB（candles 表按 trading_mode 过滤）行数 ≥ limit 且最新一根 open_time 距今 < 2×interval → 返 DB；否则 `adapter.get_klines` 直接透传（不落库，避免与 market_data 的 delete-and-insert 幂等窗口冲突）；交易所失败时降级返 DB 已有数据。interval→秒数映射表放 service 内常量。

**Controller 模式:** `APIRouter(prefix="/api/market", tags=["market"])`，`@api_response()`，`get_current_user` 登录可见；adapter 通过 `src/controllers/dependencies.py` 既有 `get_adapter` 依赖注入（执行时核对该依赖名，与 account.py 用法一致）。

**Steps:** service 单测红灯（DB 足够新→不调 adapter；DB 陈旧→调 adapter stub；白名单校验抛 ParamsException）→ 实现 → API 测试（沿用 test_read_endpoints.py fixture 模式 + 匿名 400003）→ 绿灯 → `git commit -m "feat(market): K线查询端点 GET /api/market/klines"` + push。

---

### Task 3: GET /api/market/ticker + GET /api/market/symbols

**Files:**
- Modify: `backend/src/services/execution/market_query.py`
- Modify: `backend/src/controllers/api/v1/market/market.py`
- Modify: `backend/src/cruds/regime_crud.py`（加 `find_latest_by_symbol(session, *, trading_mode, symbol)`）
- Test: 追加到 Task 2 两个测试文件

**契约:**

`GET /api/market/ticker?symbol=BTCUSDT` →

```json
{"symbol": "BTCUSDT", "last_price": 50000.0, "price_change_pct": -0.021,
 "high_24h": 51000.0, "low_24h": 49000.0, "volume_24h": 12345.6, "quote_volume_24h": 61728.0,
 "mark_price": null, "index_price": null, "funding_rate": null,
 "next_funding_time": null, "open_interest": null}
```

（后五个字段来自 `get_futures_metrics`，不可用即 null。）

`GET /api/market/symbols` → 遍历 `symbol_config.enabled=True`（按 sort_order, priority）:

```json
[{"symbol": "BTCUSDT", "base_asset": "BTC", "last_price": 50000.0,
  "price_change_pct": 0.012, "quote_volume_24h": 61728.0,
  "has_position": true, "regime": "trending_up"}]
```

单 symbol 行情失败 → 该行情字段 null（不整体失败）；`has_position` 查 OPEN Position；`regime` 取最新 RegimeSnapshot（无则 null）。

**Steps:** 红灯 → 实现 → 绿灯 → `git commit -m "feat(market): 自选列表与 24h ticker 端点（含 USDT-M 公共指标）"` + push。

---

### Task 4: 守卫重构 — evaluate() 逐项结果，check() 在其上重建

**Files:**
- Modify: `backend/src/services/execution/execution_guard.py`
- Test: `backend/tests/unit/execution/test_execution_guard.py`（追加；既有 21 用例必须原样全绿）

**设计:**

```python
@dataclass
class GuardCheckResult:
    check: str                       # 规则名: daily_loss/consecutive_losses/balance/
                                     # duplicate_position/position_size/single_risk/
                                     # sl_distance/rr_ratio/chaotic_regime/review
    passed: bool
    note: str
    severity: Literal["REJECT", "DEGRADE"] = "REJECT"   # 未通过时的裁决级别

def evaluate(self, *, proposal, trading_mode, current_price, regime,
             available_usdt, daily_pnl, daily_pnl_pct, atr,
             review_rejected=False) -> list[GuardCheckResult]:
    """跑全部规则（不短路、不写审计、不发事件）, 按现有 1-10 顺序返回逐项结果。
    HOLD 返回空列表（无规则可查）。"""
```

`check()` 改为：调 `evaluate()` → 按顺序取第一个 `passed=False` 的项定裁决（severity=DEGRADE → DEGRADE+HOLD，否则 REJECT；全过 → PASS）→ 原样走 `_record()`（risk_events + outbox 事件），**reason 字符串与现有格式逐字一致**（既有测试断言 reason 前缀）。CLOSE_LONG 只跑规则 1/2/9/10（与现状一致：仓位/风险/SL/RR 仅 OPEN_LONG）。

**等价性测试（roadmap P2 验收核心）:**

```python
@pytest.mark.parametrize("scenario", [...])   # 覆盖: 干净PASS/日亏/连亏/余额不足/重复持仓/
                                              # 超仓/单笔风险/SL距离/RR/chaotic/review_rejected
def test_check_verdict_equals_first_failed_evaluate_item(session, profile, scenario):
    """check() 的裁决必须等于 evaluate() 首个未通过项的 severity 推导结果。"""
```

**Steps:** 红灯（evaluate 不存在）→ 重构 → 全量守卫测试绿（21 旧 + 新增）→ `git commit -m "refactor(risk): 守卫拆出 evaluate() 逐项结果，check() 行为不变"` + push。

---

### Task 5: ManualTradeService.precheck + POST /api/orders/precheck

**Files:**
- Create: `backend/src/services/execution/manual_trade.py`
- Create: `backend/src/schemas/manual_order.py`（`ManualOrderCreate`：symbol/side/type/qty/price?/sl?/tp?/reduce_only/client_order_id?）
- Create: `backend/src/controllers/api/v1/execution/orders.py`（`APIRouter(prefix="/api/orders")`）
- Modify: `backend/src/controllers/router.py`
- Test: `backend/tests/unit/execution/test_manual_trade.py` + `backend/tests/api/test_orders_api.py`

**precheck 逻辑（`ManualTradeService(session, adapter)`）:**

1. 组装上下文：current_price=`adapter.get_ticker`；available/daily_pnl=`AccountStateService.get_current_balance_usdt`+`get_daily_pnl`；atr=最新 IndicatorSnapshot（无则 0）；regime=最新 RegimeSnapshot（无则 None→chaotic 规则视为通过，note 标 "no regime data"）
2. HALTED：`KillSwitchService.should_block_new_trades()` → `halted=True`；halted 且非（SELL+reduce_only）→ 在 checks 首位插入 `{check: "kill_switch", passed: False, note: "halted"}` 并 verdict=REJECT
3. side 映射：BUY→`DecisionProposal(action="OPEN_LONG", source="manual", position_size_pct=qty*price/available, entry_price=当前价或 body.price, stop_loss=body.sl, take_profit=body.tp)`；SELL→CLOSE_LONG（须存在 OPEN position，否则 REJECT `{check: "position_exists", ...}`）
4. `guard.evaluate(...)` → checks；verdict 推导与 Task 4 同一函数
5. 返回 `{verdict, halted, checks: [{check, pass, note}], context: {current_price, available_usdt, atr, regime}}`

**Controller:** `POST /api/orders/precheck`（admin），LIMIT type 不在此拦（预检只评估风控）。

**Steps:** 红灯 → 实现 → 绿灯（含：halted+BUY 拒 / halted+SELL+reduce_only 过 / 无持仓 SELL 拒）→ `git commit -m "feat(execution): 手动下单守卫预检 POST /api/orders/precheck"` + push。

---

### Task 6: 手动下单 POST /api/orders（共用执行内核）

**Files:**
- Modify: `backend/src/services/execution/order_executor.py`（提取 `_execute_open_order` / 复用 close 内核，加 `manual_open` / `manual_close`，参数含显式 qty + 外部 trace_id + `ai_decision_id=None`；事件照发）
- Modify: `backend/src/services/execution/manual_trade.py`（`place_order(user_id, body)`）
- Modify: `backend/src/controllers/api/v1/execution/orders.py`（`POST ""`）
- Modify: `backend/src/core/trace/trace_id.py`（加 `make_manual_trace_id(user_id, client_order_id) = sha256(f"manual:{user_id}:{client_order_id}")[:32]`）
- Test: 追加两个测试文件

**place_order 流程（服务端不信任预检结果）:**

1. `type=="LIMIT"` → `ServiceException("LIMIT 暂不支持，V0.1 手动单为市价")`
2. `client_order_id` 缺省 → uuid4 hex；trace_id=`make_manual_trace_id`；**幂等**：orders.trace_id 已存在 → 返回既有订单（HTTP 层同样 200）
3. 重跑 precheck；verdict != PASS → `RiskRejectedException(第一个未过项 note)`
4. BUY → `manual_open`（显式 qty 下市价单，写 Order+Position，SL/TP 存 Position 由监控执行）；SELL → `manual_close`（平既有 OPEN position，写 Order+Trade）
5. 写 audit_logs（参照 `manual_ops._audit_and_emit` 模式：operator_user_id + action="manual_order" + reason）+ outbox `manual.override` 事件
6. 返回 `{order_id, trace_id, status, position_id?, trade_id?}`

**测试要点:** 幂等（同 client_order_id 两次 → 同 order_id）；REJECT 场景不产生 Order 行；HALTED 非 reduce_only 拒（roadmap 验收）；BUY 成功写 Position + 事件。

**Steps:** 红灯 → 实现 → 绿灯 + OrderExecutor 既有测试零回归 → `git commit -m "feat(execution): 手动下单 POST /api/orders（幂等+复检守卫+审计）"` + push。

---

### Task 7: PATCH /api/positions/{id}/sltp

**Files:**
- Modify: `backend/src/services/execution/manual_trade.py`（`update_sltp(user_id, position_id, sl, tp)`）
- Modify: `backend/src/controllers/api/v1/execution/positions.py`（加 PATCH 路由，admin）
- Test: 追加 `tests/unit/execution/test_manual_trade.py` + `tests/api/test_orders_api.py`

**校验（与守卫规则 7 同逻辑）:** position 必须 OPEN 且 trading_mode 匹配；`sl < current_price`（多头）且 SL 距离在 `[sl_atr_min_mult, sl_atr_max_mult]×ATR`（ATR 缺失时跳过距离校验只查方向）；`tp > current_price`（给 tp 时）。通过 → 更新 Position + audit_logs + outbox `position.updated`。失败 → `RiskRejectedException`。

**Steps:** 红灯 → 实现 → 绿灯 → `git commit -m "feat(execution): 持仓 SL/TP 修改 PATCH /api/positions/{id}/sltp（走守卫规则+审计）"` + push。

---

### Task 8: 全量回归 + lint + worklog 收口

1. `cd backend && uv run pytest -q` → ≥543+新增 全绿
2. `uv run ruff check src/ tests/` → 0 警告
3. worklog `docs/worklog/20260705_<HHMM>_handoff后端P2_行情与手动下单.md`（含"现货执行 + USDT-M 公共行情"口径决策记录）
4. commit + push

---

## Self-Review 结论

1. **规格覆盖**：3.1 的 symbols/klines/ticker ✅（WS 代理明确拆 P2b）；3.2 的 precheck/orders/sltp ✅（同一 guard、manual trace 幂等、HALTED reduce-only）✅
2. **占位符**：Task 4-7 为重构类任务，给出的是接口契约+行为规范级代码（执行者即本会话，实现细节以现有 order_executor/manual_ops 代码为准，符合仓库"实用主义优于教条"）
3. **类型一致性**：GuardCheckResult 在 Task 4 定义、Task 5/6 复用；verdict 推导单一函数两处共用 ✅
