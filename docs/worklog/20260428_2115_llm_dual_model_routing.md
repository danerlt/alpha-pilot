# LLM 双模型 (strong/fast) 路由能力落地

时间：2026-04-28 21:15

## 做了什么

1. **新增 `LLMClients` dataclass + `build_llm_clients()` factory**
   - 文件：`backend/src/strategy/ai_trader/llm_client.py`
   - 暴露 tier 路由：`clients.get("strong" | "fast")`
   - fast 模型留空 / 与 strong 同名 → fast 复用 strong 实例（不重复构造 OpenAIClient）
   - 同时新增 `LLMTier = Literal["strong","fast"]` 类型别名

2. **`scheduler_jobs._build_llm_clients(settings)` 替代旧 `_build_llm`**
   - 文件：`backend/src/workers/scheduler_jobs.py`
   - 占位 key 时两 tier 都回退同一个 `MockLLMClient`
   - 真实 key 时调 `build_llm_clients()` 把 `LLM_MODEL` / `LLM_MODEL_FAST` 都装配好
   - 旧 `_build_llm()` 改为 thin wrapper（取 strong），保留以兼容已有测试 monkeypatch
   - `new_strategy_pipeline_job` 显式调 `_build_llm_clients`，主决策仍传 strong（pipeline 当前唯一消费方）

3. **`decision_engine.engine._call_llm` 加 `tier` 参数**
   - 文件：`backend/src/services/decision_engine/engine.py`
   - 新增 `_resolve_model(settings, tier)` 纯函数：fast 缺失时回退 strong
   - `_call_llm(system, user, *, tier="strong")` 默认行为不变；轻量调用方传 `tier="fast"` 即可走 `LLM_MODEL_FAST`

## 为什么这样做

调研后发现：当前后端**所有**真实 LLM 调用点都是高价值核心决策路径（`DecisionSolver` 和旧 `decision_engine.engine`）；regime / experience / reporting / review_critic 全是规则/数据查询，没有现成的轻量 LLM 场景可以路由到 fast 模型。

按老板任务要求中的"实用主义"指引：
- **不强造**假的轻量调用点（避免过度设计）
- 但**把双 tier 接口能力做扎实**：factory + dict 容器 + tier 参数都已就位
- `LLM_MODEL_FAST` 已是真实可调用的 API 表面：`scheduler_jobs._build_llm_clients` 在生产路径上构造它，`decision_engine._call_llm(tier="fast")` 是公开调用入口
- 兜底逻辑严格：fast 留空 / 同名 / 字段缺失三种 case 都安全回退到 strong

未来出现具体轻量场景（解析 raw_output 重试、experience 总结、daily report narrative 等）时，调用方传 `tier="fast"` 一行即可启用，无需再改装配层。

## 如何验证

1. 单元测试：`cd backend && uv run python -m pytest -q --ignore=tests/integration`
   - **结果：408 passed**（无新增 failure）
2. 新增覆盖：
   - `tests/unit/strategy/ai_trader/test_llm_client.py`：factory 双客户端构造 + fast 三种回退 case + `LLMClients.get()` 默认 strong
   - `tests/unit/workers/test_scheduler_jobs.py`：占位 key 双 tier 都回退 mock + 非占位 key + fast 留空回退 strong
   - `tests/unit/test_decision_engine_tier.py`：`_resolve_model` 四种路由 case

## 对应 commit

`3c7b732 feat(llm) 引入 strong/fast 双 tier 客户端路由能力`

## 未解决 / 后续

- 当前没有任何代码实际调用 `tier="fast"`，相关代码路径尚未在生产中执行过。等出现首个轻量场景（候选：experience_store 的 summary、reporting 的 narrative、parser 重试降级）时再接入。
- `_build_llm` 兼容 wrapper 在所有调用方都迁移到 `_build_llm_clients` 后可移除（当前测试和老路径还在用）。
