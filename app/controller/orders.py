"""Order API boundary. Pseudocode only."""

def order_detail(order_id, current_user):
    return order_service.get_detail(current_user.id, order_id)


def change_order_status(order_id, target_status, current_user, idempotency_key):
    return order_service.transition(
        current_user.id,
        order_id,
        target_status,
        idempotency_key,
    )
