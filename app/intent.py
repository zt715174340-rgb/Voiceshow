"""Intent Agent: model decides intent; rules extract and validate slots."""

ALLOWED_INTENTS = {
    "product_recommendation", "product_compare", "product_price_query",
    "product_availability_query", "product_detail_query",
    "order_history_query", "order_detail_query", "logistics_query",
    "after_sales_query", "knowledge_query", "change_preference",
    "chitchat", "greeting", "unknown",
}


def classify_intent(session_id: str, query: str):
    cached = intent_cache.get(session_id, fingerprint(query))
    if cached:
        return cached

    history = recent_turns(session_id, agent_name="intent")
    raw = llm.json_call(INTENT_PROMPT, {
        "history": history,
        "query": query,
        "allowed_intents": sorted(ALLOWED_INTENTS),
    })
    result = parse_and_validate_intent(raw) or unknown_intent(query)
    result.slots = merge_model_and_rule_slots(
        result.slots,
        extract_slots_by_rule(query),
    )
    result = revise_intent_by_context(result, history)
    intent_cache.set(session_id, fingerprint(query), result, ttl=300)
    return result


def revise_intent_by_context(result, history):
    if has_price_question(result, history):
        result.intent = "product_price_query"
    if has_explicit_negation(result) and last_recommendation(history):
        result.intent = "change_preference"
    return result
