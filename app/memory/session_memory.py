"""Redis-backed session memory. Pseudocode only."""

def load_recent(session_id, agent_name):
    policy = memory_policy.for_agent(agent_name)
    return redis_memory.tail(session_id, policy.max_turns)


def save_turn(session_id, role, content):
    redis_memory.append(session_id, role, content, ttl=1800)
