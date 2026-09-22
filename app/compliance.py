"""Input/output safety and evidence checks. Pseudocode only."""

def check_input(text: str):
    risk = policy_engine.scan(text)
    if risk.level == "blocked":
        return ToolResult(ok=False, error_code="INPUT_BLOCKED")
    return risk


def check_output(answer: str, evidence: list):
    if contains_sensitive_content(answer):
        return safe_template("OUTPUT_BLOCKED")
    if contains_unsupported_claim(answer, evidence):
        return safe_template("NO_EVIDENCE")
    return answer
