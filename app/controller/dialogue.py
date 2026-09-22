"""Dialogue API boundary. Pseudocode only."""

async def chat(request, current_user):
    state = await session_service.load(request.session_id, current_user.id)
    result = await orchestrator.handle(state, request.message)
    return DialogueResponse.from_result(result)
