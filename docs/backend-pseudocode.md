# Backend contract pseudocode

This file records the next backend boundary without pretending that authentication,
payment, or fulfillment is already production-ready.

```python
POST /api/auth/register
    validate email and password
    hash password with Argon2/bcrypt
    create user
    return access_token

POST /api/auth/login
    verify password hash
    issue short-lived access_token and refresh_token

require_permission("orders:read")
GET /api/orders/{order_no}
    return order owned by current_user

POST /api/orders/{order_no}/transition
    allowed = {
        "PENDING_PAYMENT": {"PAID", "CANCELLED"},
        "PAID": {"SHIPPED", "CANCELLED"},
        "SHIPPED": {"COMPLETED"},
        "COMPLETED": set(),
        "CANCELLED": set(),
    }
    assert next_status in allowed[current_status]
    update status and append an audit event
```

The current demo keeps `user_id=1` and `CREATED` orders. The contract above is a
design skeleton for later replacement with JWT, a permission middleware, payment
callbacks, and a real order state machine.
