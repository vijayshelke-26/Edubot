"""
LLM-powered response generation using Google Gemini.
Falls back to retrieval-based responses if Gemini is unavailable.
"""

import logging
import os
import time
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client = None
_available = None


def _init():
    """Initialize Gemini client (lazy, once)."""
    global _client, _available
    if _available is not None:
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.info("No GEMINI_API_KEY found — using retrieval-based responses.")
        _available = False
        return

    try:
        from google import genai

        _client = genai.Client(api_key=api_key)
        # Verify key format without wasting a quota call
        _client.models.list()
        _available = True
        logger.info("Gemini connected successfully.")
    except Exception as e:
        logger.warning("Gemini init failed: %s", e)
        _available = False


def is_available() -> bool:
    """Check if LLM is available."""
    _init()
    return _available


_TUTORIAL_CUES = (
    "tutorial", "curriculum", "course", "roadmap",
    "step by step", "step-by-step", "from scratch",
    "follow daily", "daily plan", "daily lesson",
    "walk me through", "guide me through",
    "teach me python from scratch", "learn python from scratch",
    "30 day", "30-day", "7 day", "7-day",
)


def _is_tutorial_request(text: str, chat_history: list[dict] | None = None) -> bool:
    """Detect requests for a multi-day curriculum rather than a one-off answer."""
    t = (text or "").lower()
    if any(cue in t for cue in _TUTORIAL_CUES):
        return True
    # "i want to learn python/programming" with no specific concept = tutorial-like
    if ("want to learn" in t or "wanna learn" in t) and ("python" in t or "programming" in t):
        return True
    return False


_DAY_HEADING_RE = __import__("re").compile(r"###\s*Day\s*(\d+)\s*:", __import__("re").IGNORECASE)


def _next_day_number(chat_history: list[dict] | None) -> int:
    """If we've already delivered a `### Day N:` lesson, the next reply is Day N+1."""
    if not chat_history:
        return 1
    last_day = 0
    for msg in chat_history:
        if msg.get("role") != "bot":
            continue
        for match in _DAY_HEADING_RE.finditer(msg.get("content", "")):
            last_day = max(last_day, int(match.group(1)))
    return last_day + 1 if last_day else 1


def generate_response(
    question: str,
    kb_answer: str,
    complexity_level: str,
    intent: str,
    chat_history: list[dict] | None = None,
) -> str | None:
    """
    Generate a natural response using Gemini with conversation context.

    Args:
        question: The student's original question
        kb_answer: The retrieved answer from knowledge base (used as context)
        complexity_level: beginner/intermediate/advanced
        intent: The classified intent
        chat_history: Recent chat messages [{"role": "user"/"bot", "content": "..."}]

    Returns:
        Generated response string, or None if LLM is unavailable.
    """
    _init()
    if not _available or not _client:
        return None

    level_instructions = {
        "beginner": "Explain in very simple terms using everyday analogies. Avoid jargon. Use short sentences. Give a simple code example if relevant.",
        "intermediate": "Give a clear technical explanation with proper terminology. Include a practical code example. Mention related concepts briefly.",
        "advanced": "Give a deep, detailed explanation covering internals, edge cases, and best practices. Include advanced code examples. Reference design patterns or performance considerations where relevant.",
    }

    level_guide = level_instructions.get(complexity_level, level_instructions["beginner"])

    # Build conversation context from chat history
    history_text = ""
    if chat_history:
        recent = chat_history[-6:]  # Last 3 exchanges
        history_lines = []
        for msg in recent:
            role = "Student" if msg["role"] == "user" else "You"
            # Truncate long bot responses in history
            content = msg["content"][:200] if msg["role"] == "bot" else msg["content"]
            history_lines.append(f"{role}: {content}")
        history_text = "\n".join(history_lines)

    history_block = (
        "Recent conversation:\n" + history_text + "\n" if history_text else ""
    )

    if _is_tutorial_request(question, chat_history):
        day_num = _next_day_number(chat_history)
        if day_num == 1:
            prompt = f"""You are an educational programming tutor. The student wants a multi-day Python tutorial they can follow daily — NOT a one-off answer.

Student's level: {complexity_level}
Student's current message: {question}

{history_block}Produce ONE response with this exact structure and markdown formatting:

### Your Python Plan
One short sentence acknowledging the goal. No flattery, no metaphors.

### Curriculum (Days 1-10)
A numbered markdown list of 10 day titles. Cover, in order:
1. Setup + first script (print, comments)
2. Variables and data types
3. Strings and user input
4. Conditionals (if/elif/else)
5. Loops (for, while)
6. Lists and dictionaries
7. Functions
8. Files and modules
9. Error handling
10. A small project (e.g. a number-guessing game)

### Setup (do this before Day 1)
2-3 short lines: install Python from python.org, pick an editor (VS Code or IDLE) OR use an online REPL like replit.com. Show the one-line command to verify install (`python --version` or `python3 --version`).

### Day 1: Your First Script
- 2-3 sentences explaining `print()` and comments.
- One runnable code block with `print(...)` and a `#` comment.
- An **Exercise:** one short task for the student to try (e.g. print their name and favorite language on two lines).

### Next
End with: *"Reply 'Day 2' when you've finished the exercise and I'll continue."*

Hard rules:
- Do NOT start with "Sure!", "Great question!", "That's a wonderful plan!" or any flattery.
- Do NOT use the chef/recipe analogy or other filler metaphors.
- Keep prose tight. Code blocks must be valid Python.
- Use markdown headings exactly as shown above."""
        else:
            prompt = f"""You are an educational programming tutor running a daily Python tutorial.

Student's level: {complexity_level}
Student's current message: {question}

{history_block}The student has completed earlier days and is ready for **Day {day_num}**. Look at the recent conversation to figure out which topic comes next in the curriculum (Days 1-10 cover: setup, variables, strings/input, conditionals, loops, lists/dicts, functions, files/modules, error handling, small project).

Produce ONE response with this structure:

### Day {day_num}: <topic title>
- 3-5 sentences explaining the concept clearly at {complexity_level} level.
- One runnable Python code block demonstrating it.
- An **Exercise:** one short hands-on task.

### Next
End with: *"Reply 'Day {day_num + 1}' when you've finished the exercise."*

Hard rules:
- No flattery openers.
- No filler metaphors.
- Code blocks must be valid Python.
- Use markdown headings exactly as shown."""
    else:
        prompt = f"""You are an educational programming chatbot helping a college student learn programming.

Student's level: {complexity_level}
Student's current message: {question}

{history_block}Reference knowledge (use as context but explain naturally):
{kb_answer}

Instructions:
- {level_guide}
- Be conversational and encouraging — like a friendly tutor.
- Keep the response concise (3-6 sentences for beginner, 5-8 for intermediate, 6-10 for advanced).
- If relevant, include a small code example in Python.
- IMPORTANT: Answer the student's CURRENT message in the context of the conversation above. If they ask a follow-up like "how many are there?" or "can you list them?", refer to the topic from the conversation.
- Do NOT start with "Sure!" or "Great question!" — start directly with the explanation.
- Do NOT mention that you are using reference knowledge or a knowledge base.
- Use markdown formatting for code blocks and bold terms."""

    # Retry once after a short wait if rate-limited
    for attempt in range(2):
        try:
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and response.text:
                return f"💻 **Programming** | *{complexity_level} level*\n\n{response.text.strip()}"
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                time.sleep(5)
                continue
            logger.error("Gemini generation failed: %s", e)
            break

    return None
