import logging

from models import db
from models.chat import ChatSession, ChatMessage
from models.progress import UserProgress
from nlp.pipeline import process_message
from services.mastery_service import log_chat_topics

logger = logging.getLogger(__name__)


def get_or_create_session(user_id: int, session_id: int | None = None) -> ChatSession:
    """Get existing session or create a new one."""
    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        if session:
            return session

    session = ChatSession(user_id=user_id)
    db.session.add(session)
    db.session.commit()
    return session


def get_user_levels(user_id: int) -> dict[str, str]:
    """Get user's complexity level per domain from progress."""
    progress = UserProgress.query.filter_by(user_id=user_id).all()
    return {p.domain: p.current_level for p in progress}


def handle_message(user_id: int, text: str, session_id: int | None = None) -> dict:
    """Process a user message through the NLP pipeline and store both messages."""
    logger.info("handle_message: user_id=%s session_id=%s", user_id, session_id)
    session = get_or_create_session(user_id, session_id)
    user_levels = get_user_levels(user_id)

    # Track topics from the user's message
    log_chat_topics(user_id, text)

    # Get recent chat history for context
    recent_messages = (
        ChatMessage.query.filter_by(session_id=session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )
    chat_history = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_messages)
    ]

    # Run NLP pipeline
    result = process_message(text, session.id, user_levels, chat_history)

    # Store user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=text,
        detected_domain=result["detected_domain"],
        detected_intent=result["detected_intent"],
        complexity_level=result["complexity_level"],
    )
    db.session.add(user_msg)

    # Store bot response
    bot_msg = ChatMessage(
        session_id=session.id,
        role="bot",
        content=result["response"],
        detected_domain=result["detected_domain"],
        detected_intent=result["detected_intent"],
        complexity_level=result["complexity_level"],
    )
    db.session.add(bot_msg)
    db.session.commit()

    logger.info(
        "handle_message complete: session_id=%s intent=%s domain=%s level=%s",
        session.id, result["detected_intent"], result["detected_domain"],
        result["complexity_level"],
    )
    return {
        "session_id": session.id,
        "user_message": user_msg.to_dict(),
        "bot_message": bot_msg.to_dict(),
    }
