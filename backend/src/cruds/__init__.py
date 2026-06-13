"""所有实体 crud 单例集中导出。"""
from src.cruds.account_crud import account_snapshot_crud
from src.cruds.account_entity_crud import account_crud, parameter_version_crud, risk_profile_crud
from src.cruds.agent_invocation_crud import agent_invocation_crud
from src.cruds.attribution_crud import strategy_score_crud, trade_attribution_crud
from src.cruds.audit_log_crud import audit_log_crud
from src.cruds.base_crud import BaseCrud
from src.cruds.candle_crud import candle_crud
from src.cruds.decision_crud import ai_decision_crud
from src.cruds.decision_review_crud import decision_review_crud
from src.cruds.event_store_crud import event_inbox_crud, event_outbox_crud
from src.cruds.experience_crud import experience_record_crud
from src.cruds.experience_v2_crud import experience_summary_crud, experience_v2_crud
from src.cruds.factor_crud import (
    factor_candidate_crud,
    factor_definition_crud,
    factor_snapshot_crud,
)
from src.cruds.indicator_crud import indicator_snapshot_crud
from src.cruds.ops_diagnosis_crud import ops_diagnosis_crud
from src.cruds.order_crud import order_crud
from src.cruds.position_crud import position_crud
from src.cruds.prompt_crud import prompt_template_crud, proposal_draft_crud
from src.cruds.regime_crud import regime_snapshot_crud
from src.cruds.report_crud import daily_report_crud
from src.cruds.risk_event_crud import risk_event_crud
from src.cruds.shadow_crud import shadow_decision_crud, shadow_evaluation_crud
from src.cruds.symbol_config_crud import symbol_config_crud
from src.cruds.system_setting_crud import system_setting_crud
from src.cruds.trade_crud import trade_crud
from src.cruds.user_crud import user_crud

__all__ = [
    "BaseCrud",
    "account_crud",
    "account_snapshot_crud",
    "agent_invocation_crud",
    "ai_decision_crud",
    "audit_log_crud",
    "candle_crud",
    "daily_report_crud",
    "decision_review_crud",
    "event_inbox_crud",
    "event_outbox_crud",
    "experience_record_crud",
    "experience_summary_crud",
    "experience_v2_crud",
    "factor_candidate_crud",
    "factor_definition_crud",
    "factor_snapshot_crud",
    "indicator_snapshot_crud",
    "ops_diagnosis_crud",
    "order_crud",
    "parameter_version_crud",
    "position_crud",
    "prompt_template_crud",
    "proposal_draft_crud",
    "regime_snapshot_crud",
    "risk_event_crud",
    "risk_profile_crud",
    "shadow_decision_crud",
    "shadow_evaluation_crud",
    "strategy_score_crud",
    "symbol_config_crud",
    "system_setting_crud",
    "trade_attribution_crud",
    "trade_crud",
    "user_crud",
]
