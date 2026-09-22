"""User profile aggregation and recommendation reranking."""

def record_behavior(user_id, product_id, behavior, context):
    behavior_repo.insert(user_id, product_id, behavior, context)
    profile_events.publish("USER_BEHAVIOR", {"user_id": user_id, "behavior": behavior})


def rebuild_profile(user_id):
    events = behavior_repo.list_recent(user_id, days=90)
    return profile_repo.upsert(
        user_id=user_id,
        preferred_categories=weighted_categories(events),
        preferred_brands=weighted_brands(events),
        price_range=weighted_price_range(events),
        negative_preferences=extract_negative_preferences(events),
    )


def profile_score(product, profile) -> float:
    return category_match(product, profile) + brand_match(product, profile) - negative_match(product, profile)
