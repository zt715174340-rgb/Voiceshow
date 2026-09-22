"""Intent DTOs equivalent to the original IntentResult."""

class IntentResult:
    intent: str
    slots: dict
    confidence: float
    source: str


class SlotUpdate:
    name: str
    value: object
    operation: str  # SET / APPEND / REMOVE / RESET
