"""AlphaPilot event bus primitives: IDs, contracts, bus, outbox, inbox.

The event bus sits between the four planes (Control / Strategy / Execution /
Insight). Everything else under src/events/ either defines contracts or
implements transport.
"""
