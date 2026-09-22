"""Authentication and permission boundaries. Pseudocode only."""

def register(email: str, password: str):
    validate_email(email)
    validate_password_strength(password)
    user = user_repo.create(email=email, password_hash=hash_password(password))
    return issue_access_token(user.id)


def login(email: str, password: str):
    user = user_repo.find_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("INVALID_CREDENTIALS")
    return issue_access_token(user.id)


def get_current_user(access_token: str):
    payload = jwt.verify(access_token, settings.jwt_secret)
    return user_repo.get(payload["user_id"])


def require_permission(user, permission: str):
    if permission not in user.permissions:
        raise PermissionError(permission)
