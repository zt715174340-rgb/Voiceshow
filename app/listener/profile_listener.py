"""Asynchronous profile and audit listeners. Pseudocode only."""

async def on_user_behavior(event):
    await profile_service.update_from_behavior(event)
    await audit_service.record(event)
