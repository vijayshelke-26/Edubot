import json
import os
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nlp.preprocessor import preprocess
from nlp.llm_generator import generate_response, is_available as llm_available

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
_knowledge_base: dict[str, list] = {}
_vectorizers: dict[str, TfidfVectorizer] = {}
_tfidf_matrices: dict[str, object] = {}
_questions_processed: dict[str, list[str]] = {}

GREETING_RESPONSES = [
    "Hello! I'm your programming assistant. Ask me anything about coding, data structures, algorithms, OOP, and more — or request a quiz!",
    "Hi there! Ready to learn? Ask me about any programming topic — Python, loops, functions, OOP, and beyond.",
    "Hey! Welcome back. What programming topic would you like to study today?",
]

FAREWELL_RESPONSES = [
    "Goodbye! Keep learning and practicing. See you next time!",
    "Bye! Great study session. Come back whenever you need help!",
    "See you later! Remember to take quizzes to test your knowledge.",
]

THANKS_RESPONSES = [
    "You're welcome! Let me know if you have more questions.",
    "Happy to help! Feel free to ask anything else.",
    "Glad I could help! Keep up the great learning!",
]

HELP_RESPONSE = (
    "Here's what I can do:\n\n"
    "**Ask Questions** - Ask me about any programming topic — variables, loops, OOP, data structures, algorithms, and more.\n"
    "**Take Quizzes** - Say 'quiz me' or 'start a quiz' to test your programming knowledge.\n"
    "**Check Progress** - Say 'show my progress' to see your learning stats.\n\n"
    "I adapt my explanations based on your quiz performance - "
    "the better you score, the more advanced my explanations become!"
)

FALLBACK_RESPONSES = [
    "I'm not sure I understand that. Could you rephrase your question? I can help with programming topics like variables, loops, OOP, and algorithms.",
    "I couldn't find a good match for that question. Try asking about a specific topic like variables, functions, data structures, or sorting algorithms.",
    "Hmm, I'm not confident about that one. Could you be more specific? I specialize in programming concepts and coding topics.",
]


def _load_domain(domain: str):
    """Load and index a domain's knowledge base for similarity search."""
    if domain in _knowledge_base:
        return

    filepath = os.path.join(_DATA_DIR, f"{domain}.json")
    if not os.path.exists(filepath):
        _knowledge_base[domain] = []
        return

    with open(filepath) as f:
        entries = json.load(f)

    _knowledge_base[domain] = entries
    processed = [preprocess(entry["question"]) for entry in entries]
    _questions_processed[domain] = processed

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(processed)
    _vectorizers[domain] = vectorizer
    _tfidf_matrices[domain] = matrix


def select_response(
    text: str, domain: str, intent: str, complexity_level: str = "beginner",
    chat_history: list[dict] | None = None,
    original_question: str | None = None,
) -> str:
    """Select a response based on intent and domain."""
    if intent == "greeting":
        return random.choice(GREETING_RESPONSES)
    if intent == "farewell":
        return random.choice(FAREWELL_RESPONSES)
    if intent == "thanks":
        return random.choice(THANKS_RESPONSES)
    if intent == "help":
        return HELP_RESPONSE
    if intent == "request_quiz":
        return "Sure! Let's test your programming knowledge. Head over to the Quiz section to begin, or I can give you a quick question here."
    if intent == "check_progress":
        return "You can check your detailed progress on the Progress page. It shows your quiz scores, current level, and performance history!"

    # For ask_question intent, find the best matching answer
    if domain == "general":
        return random.choice(FALLBACK_RESPONSES)

    _load_domain(domain)
    entries = _knowledge_base.get(domain, [])
    if not entries:
        return random.choice(FALLBACK_RESPONSES)

    processed_query = preprocess(text)
    query_vec = _vectorizers[domain].transform([processed_query])
    similarities = cosine_similarity(query_vec, _tfidf_matrices[domain])[0]
    best_idx = similarities.argmax()
    best_score = similarities[best_idx]

    # Get KB answer as context (even for LLM)
    if best_score < 0.15:
        kb_answer = None
    else:
        entry = entries[best_idx]
        kb_answer = entry["answers"].get(complexity_level, entry["answers"]["beginner"])

    # Try LLM-generated response
    if llm_available():
        context = kb_answer or f"The student is asking about: {text}. This is a programming topic."
        actual_question = original_question or text
        llm_response = generate_response(
            actual_question, context, complexity_level, "ask_question",
            chat_history=chat_history,
        )
        if llm_response:
            return llm_response

    # Fallback: retrieval-based response
    if kb_answer is None:
        return (
            f"I don't have a specific answer for that in **{domain}**, but try asking "
            f"about a related topic. Here are some areas I cover well in {domain}!"
        )

    return f"💻 **{domain.title()}** | *{complexity_level} level*\n\n{kb_answer}"
