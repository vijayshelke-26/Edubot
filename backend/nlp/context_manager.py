"""Tracks conversation context per chat session for follow-up questions."""

_session_contexts: dict[int, dict] = {}


def get_context(session_id: int) -> dict | None:
    """Return the last context for this session (topic, domain, etc.)."""
    return _session_contexts.get(session_id)


def set_context(session_id: int, topic: str, domain: str):
    """Store the current topic and domain for this session."""
    if topic:
        _session_contexts[session_id] = {
            "topic": topic,
            "domain": domain,
        }


def clear_context(session_id: int):
    """Clear context when a session ends."""
    _session_contexts.pop(session_id, None)
