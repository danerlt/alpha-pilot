"""Execution Core per spec §5.1.

Adapter-based exchange access, execution guard, order executor, position monitor.
All inter-plane communication goes through events; nothing here imports
Strategy Intelligence or Factor & Insight code directly.
"""
