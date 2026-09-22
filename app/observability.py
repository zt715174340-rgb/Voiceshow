"""Trace, audit and evaluation contracts. Pseudocode only."""

def record_span(trace_id, node, started_at, ended_at, input_data, output_data, status):
    trace_repo.insert({
        "trace_id": trace_id,
        "node": node,
        "started_at": started_at,
        "ended_at": ended_at,
        "input": redact_sensitive_fields(input_data),
        "output": redact_sensitive_fields(output_data),
        "status": status,
    })


def evaluate_case(case, agent_version):
    result = run_case(case, agent_version)
    return {
        "intent_correct": result.intent == case.expected_intent,
        "slot_f1": slot_f1(result.slots, case.expected_slots),
        "tool_correct": tool_match(result.tool_trace, case.expected_tools),
        "task_completed": task_completed(result, case),
    }


def regression_check(current, baseline):
    if current["task_completed"] < baseline["task_completed"] - 0.03:
        return "REGRESSION"
    return "PASS"
