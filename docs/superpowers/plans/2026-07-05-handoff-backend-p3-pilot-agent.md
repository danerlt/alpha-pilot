# Handoff 后端 P3 — Pilot AI 对话 实现计划

> 依据：handoff/03 §3.4（agent 域：SSE 流式 chat + 历史 + pending action confirm；
> 工具白名单只读为主，写操作一律生成 pending action 走人工确认，Agent 无权直改硬风控）。
> 验收（roadmap P3）：四个预设问题走通（查持仓/解释决策/风险敞口/收紧风控-需确认）；
> Agent 无法绕过 confirm 直改配置（守卫测试）。

## 设计决策

- **工具协议走 prompt-based JSON**（非 OpenAI function-calling）：现有 `LLMClient.complete()`
  是纯文本补全，prompt 协议对 DeepSeek/OpenAI/Mock 通吃且可测。模型每轮只能输出
  `{"tool": name, "args": {...}}` 或 `{"final": "回答"}`；解析失败视为 final 文本（兜底不空转）。
  工具循环上限 4 轮。
- **SSE 伪流式 V1**：`complete()` 无流式接口，final 文本按 ~64 字符切块发 `delta` 事件，
  SSE 契约（tool_call → delta → done）与真流式一致，后续换流式客户端前端无感。
- **pending action 新表 `agent_pending_actions`**（alembic revision 生成）：
  id / invocation_id / action_type("config_change") / payload_json({key,value,reason}) /
  status(PENDING|CONFIRMED|CANCELLED) / proposed_at / confirmed_by / confirmed_at。
- **可确认配置白名单** = runtime_config 四个风控键（risk.max_position_size_pct /
  max_daily_loss_pct / max_consecutive_losses / max_single_risk_pct）。
  propose 时校验 + confirm 时**再次**校验（防绕过）。confirm 复用 runtime_config 的
  `upsert_system_setting + apply_runtime_settings_refresh` 流程 + AuditLog。
- 工具白名单（只读）：get_positions / get_risk_state / get_decisions / get_decision /
  get_market_ticker / get_experiences + 唯一写口 propose_config_change（只落 pending 行）。
- LLM 装配：`dependencies.get_llm_client()`（与 scheduler `_build_llm` 同逻辑：占位 key 回退 Mock）。

## Tasks（内联 TDD，每 task 提交推送）

1. **表 + crud**：alembic revision 生成 `agent_pending_actions`；`AgentPendingAction` model
   （字段单行、无 FK）；`agent_pending_action_crud`（find_by_status / mark_confirmed）。
2. **PilotAgentService 工具层**：TOOLS 注册表 + 各只读工具（复用既有
   service/crud）+ `propose_config_change` 白名单校验；单测每个工具。
3. **chat 工具循环**：`chat(message, ...) -> Iterator[SSE事件dict]`；多轮 mock LLM 测：
   纯回答 / 工具后回答 / 提议配置 / 解析失败兜底；每次落 `agent_invocations` 行。
4. **confirm + 守卫测试**：`confirm_action(action_id, admin)`：PENDING→CONFIRMED +
   upsert + refresh + audit；重复确认报错；**非白名单键 confirm 拒绝**（Agent 绕过防线测试）。
5. **controller**：`POST /api/agent/chat`（SSE，登录）/ `GET /api/agent/history`（登录，
   typed response_model）/ `POST /api/agent/actions/{id}/confirm`（admin）；注册 router；
   API 测试（SSE 文本含 event: done / 匿名 401 / confirm 非 admin 403）。
6. 收口：全量回归 + ruff + 重导 openapi.json + worklog + 记忆。
