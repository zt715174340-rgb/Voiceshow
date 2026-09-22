"""Compliance policy boundary. Pseudocode only."""

def scan_input(text: str):
    return policy_engine.scan(text)


def scan_output(answer: str, evidence: list):
    if contains_sensitive_content(answer) or contains_unsupported_claim(answer, evidence):
        return safe_template("NO_EVIDENCE_OR_BLOCKED")
    return answer
