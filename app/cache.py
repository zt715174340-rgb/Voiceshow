"""Redis cache contracts for intent, session state and pending actions."""

def get_intent(session_id, utterance_hash):
    return redis.get(f"intent:{session_id}:{utterance_hash}")


def set_intent(session_id, utterance_hash, result, ttl=300):
    redis.setex(f"intent:{session_id}:{utterance_hash}", ttl, serialize(result))


def save_pending_order(session_id, order_preview, ttl=600):
    redis.setex(f"pending-order:{session_id}", ttl, serialize(order_preview))
