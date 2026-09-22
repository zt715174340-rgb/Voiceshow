"""Prompt version loading and prompt A/B selection. Pseudocode only."""

def load_prompt(agent_name: str, version: str = "current") -> str:
    return prompt_repository.get(agent_name, version)


def select_version(user_id: int) -> str:
    return experiment_service.bucket(user_id, "prompt_version")
