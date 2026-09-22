"""Emotion detection for response style, not for business authorization."""

def detect_emotion(query, session_id):
    history = recent_turns(session_id, agent_name="emotion")
    result = emotion_agent.detect(query, history)
    return {
        "label": result.label,
        "confidence": result.confidence,
        "response_style": style_for_emotion(result.label),
    }
