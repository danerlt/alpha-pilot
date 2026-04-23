"""Market regime classification (spec §5.3).

Input: factor snapshot; Output: one of trending_up / trending_down /
ranging / chaotic. Thresholds come from risk_profiles.regime_thresholds_json
when present (learnable), else V0.1 defaults.
"""
