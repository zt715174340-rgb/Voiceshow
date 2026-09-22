"""Short-term, long-term and per-agent memory boundaries. Pseudocode only."""

MEMORY_POLICY = {
    "intent": {"max_turns": 3, "ttl": 300},
    "recommend": {"max_turns": 8, "ttl": 1800},
    "emotion": {"max_turns": 40, "ttl": 1800},
}


def append_turn(session_id, role, content, metadata=None):
    redis.rpush(f"session:{session_id}:messages", serialize(role, content, metadata))
    redis.expire(f"session:{session_id}:messages", 1800)


def recent_turns(session_id, agent_name):
    policy = MEMORY_POLICY[agent_name]
    items = redis.lrange(f"session:{session_id}:messages", -policy["max_turns"], -1)
    return [deserialize(item) for item in items]


def summarize_old_history(session_id):
    summary = summarizer(load_old_turns(session_id))
    profile_repo.save_memory_summary(session_id, summary)
