"""Experience retrieval for prompt injection (spec §5.6).

V0.1: tag-based filter + recency ordering from the `experiences` table.
V0.2+ adds pgvector similarity search over LLM-generated summaries.
"""
