"""Clarification Agent builder. Pseudocode only."""

def build_clarify_agent():
    return Agent(name="clarify", prompt=load_prompt("clarify"), tools=[])
