"""Intent Agent builder. Pseudocode only."""

def build_intent_agent():
    return Agent(
        name="intent",
        prompt=load_prompt("intent"),
        output_schema=IntentResult,
    )
