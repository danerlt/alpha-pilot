"""AI Trader pipeline per spec §4.2.

PromptComposer → DecisionSolver → ReviewCritic → DecisionProposal.

Modules here may import from other strategy/ submodules but must not
import from execution/ / insight/ / control/ planes directly.
"""
