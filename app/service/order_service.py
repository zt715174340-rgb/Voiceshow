"""Order business service. Pseudocode only."""

def transition(user_id, order_id, target_status, idempotency_key):
    order = order_repository.find_owned(user_id, order_id)
    validate_transition(order.status, target_status)
    order_repository.update_status(order_id, target_status)
    event_bus.publish(OrderStatusChanged(order_id, target_status))
    return order
