"""Agent registry and construction boundary. Pseudocode only."""

def build_agent(name: str):
    return agent_registry[name](prompt=prompt_loader.load(name))


def build_all_agents():
    return {name: build_agent(name) for name in agent_registry.names()}
