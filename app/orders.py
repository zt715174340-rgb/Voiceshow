"""Order query and state transition service. Pseudocode only."""

ORDER_TRANSITIONS = {
    "PENDING_PAYMENT": {"PAID", "CANCELLED"},
    "PAID": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"COMPLETED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def get_order_detail(user, order_id):
    order = order_repo.find_by_id(order_id)
    if not order or order.user_id != user.id:
        return ToolResult(ok=False, error_code="ORDER_NOT_FOUND")
    return ToolResult(ok=True, data=order)


def transition_order(user, order_id, target_status, idempotency_key):
    with transaction():
        order = get_owned_order(user.id, order_id)
        if target_status not in ORDER_TRANSITIONS[order.status]:
            raise BusinessError("INVALID_ORDER_TRANSITION")
        update_order_status(order.id, target_status)
        audit_log("ORDER_STATUS_CHANGED", user.id, order.id, target_status)
        idempotency_repo.save(idempotency_key, order)
        return order
