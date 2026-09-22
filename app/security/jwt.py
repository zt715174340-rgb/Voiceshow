"""JWT and resource ownership checks. Pseudocode only."""

def issue_token(user_id: int):
    return jwt.encode({"user_id": user_id}, settings.jwt_secret)


def require_owner(user_id: int, resource):
    if resource.user_id != user_id:
        raise PermissionError("RESOURCE_FORBIDDEN")
