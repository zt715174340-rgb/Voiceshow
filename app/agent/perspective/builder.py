"""Price, scenario, quality and diversity perspective Agents."""

def build_perspective_agents():
    return {
        name: Agent(name=name, prompt=load_prompt(f"perspective/{name}"))
        for name in ["price", "scenario", "quality", "diversity"]
    }
