"""Main business orchestration service. Pseudocode only."""

async def handle(session, query):
    compliance.scan_input(query)
    intent = intent_service.classify(session.id, query)
    slots = slot_service.merge(session.slots, intent.slots)

    if clarify_service.missing_slots(intent.intent, slots):
        return clarify_service.ask(intent.intent, slots)
    return await route_intent(intent.intent, session, query, slots)
