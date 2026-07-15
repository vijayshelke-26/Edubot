import re

from nlp.intent_classifier import classify_intent
from nlp.response_selector import select_response
from nlp import context_manager

# Single domain chatbot — focused on programming
DOMAIN = "programming"

# Phrases that indicate a follow-up question about the previous topic
FOLLOWUP_PHRASES = [
    "tell me more", "more about that", "explain more", "elaborate",
    "give me an example", "can you explain", "what else", "go on",
    "continue", "more detail", "explain it", "explain that",
    "in more detail", "tell me more about that", "what do you mean",
    "i don't understand", "can you clarify", "say more",
    "expand on that", "give another example", "how does that work",
    "how many", "can you list", "what are the types",
    "what types", "list them", "show me more",
    "next step", "next lesson", "next day", "next topic", "next part",
    "what's next", "whats next", "ready for next", "next please",
]

# Matches "day 2", "day-2", "day2", etc. — used by the daily-tutorial flow.
_DAY_NUMBER_RE = re.compile(r"\bday[\s-]?\d+\b")


def _is_followup(text: str) -> bool:
    """Check if the message is a follow-up to the previous topic."""
    text_lower = text.lower().strip()
    if _DAY_NUMBER_RE.search(text_lower):
        return True
    return any(phrase in text_lower for phrase in FOLLOWUP_PHRASES)


def process_message(
    text: str, session_id: int, user_level: dict[str, str] | None = None,
    chat_history: list[dict] | None = None,
) -> dict:
    """
    Full NLP pipeline:
    1. Set domain to programming (single-domain chatbot)
    2. Classify intent
    3. Handle follow-up questions using session context
    4. Select response at appropriate complexity level (with chat history for LLM)
    """
    domain = DOMAIN
    intent, intent_conf = classify_intent(text)

    # Determine complexity level from user's progress
    complexity = "beginner"
    if user_level and domain in user_level:
        complexity = user_level[domain]

    # Handle follow-up questions: reuse the previous topic
    query_text = text
    is_followup = _is_followup(text)
    if is_followup:
        ctx = context_manager.get_context(session_id)
        if ctx and ctx.get("topic"):
            query_text = ctx["topic"]
            intent = "ask_question"
        elif chat_history:
            # Context lost (server restart) — recover topic from chat history
            for msg in reversed(chat_history):
                if msg["role"] == "user" and not _is_followup(msg["content"]):
                    query_text = msg["content"]
                    intent = "ask_question"
                    context_manager.set_context(session_id, query_text, DOMAIN)
                    break

    response = select_response(
        query_text, domain, intent, complexity,
        chat_history=chat_history,
        original_question=text if is_followup else None,
    )

    # Save the matched topic in context for future follow-ups
    if intent == "ask_question":
        context_manager.set_context(session_id, query_text, domain)

    # Clear context on farewell
    if intent == "farewell":
        context_manager.clear_context(session_id)

    return {
        "response": response,
        "detected_domain": domain,
        "detected_intent": intent,
        "complexity_level": complexity,
        "domain_confidence": 1.0,
        "intent_confidence": intent_conf,
    }
