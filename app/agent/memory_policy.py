"""Per-agent memory limits, equivalent to AgentMemoryPolicy."""

POLICY = {
    "intent": {"max_turns": 3, "ttl": 300},
    "recommend": {"max_turns": 8, "ttl": 1800},
    "emotion": {"max_turns": 40, "ttl": 1800},
}


def policy_for(agent_name: str) -> dict:
    return POLICY.get(agent_name, {"max_turns": 5, "ttl": 900})
