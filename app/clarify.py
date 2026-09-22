"""Required-slot and clarification policy. Pseudocode only."""

REQUIRED_SLOTS = {
    "product_recommendation": ["category"],
    "product_compare": ["category"],
}


def missing_slots(intent: str, slots: dict) -> list[str]:
    return [name for name in REQUIRED_SLOTS.get(intent, []) if not slots.get(name)]


def build_clarifying_question(intent: str, slots: dict) -> str:
    missing = missing_slots(intent, slots)
    if "category" in missing:
        return "您想了解哪一类商品？"
    if "budget" in missing:
        return "您的预算大概是多少？"
    return "还可以补充一下使用场景或偏好吗？"
