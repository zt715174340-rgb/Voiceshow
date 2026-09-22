"""Order persistence and ownership queries. Pseudocode only."""

def find_owned(user_id: int, order_id: str):
    return order_db.find_one(user_id=user_id, order_id=order_id)


def list_recent(user_id: int, limit: int = 10):
    return order_db.list(user_id=user_id, limit=limit, order_by="created_at DESC")
