"""Structured API response schemas. Pseudocode only."""

class DialogueResponse:
    answer: str
    intent: str
    products: list
    citations: list
    trace_id: str
