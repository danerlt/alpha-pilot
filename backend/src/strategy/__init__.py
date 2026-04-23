"""Strategy Intelligence Plane per spec §4.

AI Trader pipeline (Prompt → Decision → Review) + Program Trader (V0.2+)
+ Shadow runner (V0.3+). The plane's only outbound artifact is
DecisionProposal; downstream Execution Core consumes it without knowing
which strategy produced it.
"""
