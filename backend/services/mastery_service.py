"""
Adaptive learning algorithms: SM-2 (spaced repetition) + BKT (knowledge tracing).
Manages per-skill mastery for each user.
"""

import logging
from datetime import datetime, timedelta, timezone
from models import db
from models.mastery import UserSkillMastery, ChatTopicLog, QuizQuestionLog
from nlp.skill_tree import SKILL_TREE, get_prerequisites_met, extract_topics

logger = logging.getLogger(__name__)


# BKT default parameters (per skill)
BKT_INIT = 0.0      # P(L0): prior probability student knows the skill
BKT_TRANSIT = 0.1   # P(T): probability of learning after each attempt
BKT_SLIP = 0.1      # P(S): probability of error despite knowing
BKT_GUESS = 0.25    # P(G): probability of correct guess (1/4 for MCQ)


def _get_or_create_mastery(user_id: int, skill_id: str) -> UserSkillMastery:
    """Get or create a mastery record for a user-skill pair."""
    mastery = UserSkillMastery.query.filter_by(
        user_id=user_id, skill_id=skill_id
    ).first()
    if not mastery:
        mastery = UserSkillMastery(user_id=user_id, skill_id=skill_id)
        db.session.add(mastery)
        db.session.flush()
    return mastery


def _update_bkt(mastery: UserSkillMastery, is_correct: bool):
    """Update BKT probability of learned after an observation."""
    p_l = mastery.p_learned
    s, g = BKT_SLIP, BKT_GUESS

    if is_correct:
        p_l_given_obs = (p_l * (1 - s)) / (p_l * (1 - s) + (1 - p_l) * g)
    else:
        p_l_given_obs = (p_l * s) / (p_l * s + (1 - p_l) * (1 - g))

    # Transition: chance of learning after this attempt
    mastery.p_learned = p_l_given_obs + (1 - p_l_given_obs) * BKT_TRANSIT


def _update_sm2(mastery: UserSkillMastery, quality: int):
    """
    Update SM-2 spaced repetition parameters.
    quality: 0-5 (0=complete failure, 5=perfect)
    """
    ef = mastery.easiness_factor

    # Update easiness factor
    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    mastery.easiness_factor = max(1.3, ef)

    if quality >= 3:  # Correct
        if mastery.repetitions == 0:
            mastery.interval_days = 1
        elif mastery.repetitions == 1:
            mastery.interval_days = 6
        else:
            mastery.interval_days = round(mastery.interval_days * mastery.easiness_factor)
        mastery.repetitions += 1
    else:  # Incorrect
        mastery.repetitions = 0
        mastery.interval_days = 1

    now = datetime.now(timezone.utc)
    mastery.last_reviewed_at = now
    mastery.next_review_at = now + timedelta(days=mastery.interval_days)


def _update_mastery_level(mastery: UserSkillMastery):
    """
    Update the learner-facing mastery label conservatively.

    Mastery is treated as accumulated evidence, not a single result. A single
    correct answer is never enough to look "proficient" or "mastered": each
    higher label requires more correct answers AND good overall accuracy, and
    "mastered" additionally requires a recent run of correct answers (streak),
    so a wrong answer breaks the streak and pulls the learner back for review.
    This avoids over-claiming a learner's understanding (honest mastery
    reporting) and yields a gradual climb: attempted -> familiar -> proficient
    -> mastered over repeated correct attempts.
    """
    total = mastery.total_attempts
    if total == 0:
        mastery.mastery_level = "not_started"
        return

    correct = mastery.correct_attempts
    pct = (correct / total) * 100
    streak = mastery.streak

    if correct >= 4 and pct >= 85 and streak >= 3:
        mastery.mastery_level = "mastered"
    elif correct >= 3 and pct >= 70:
        mastery.mastery_level = "proficient"
    elif correct >= 2 and pct >= 50:
        mastery.mastery_level = "familiar"
    else:
        mastery.mastery_level = "attempted"


def update_skill_after_answer(user_id: int, skill_id: str, is_correct: bool,
                               question_text: str, difficulty: str):
    """Update all models after a quiz answer."""
    logger.info(
        "update_skill_after_answer: user_id=%s skill_id=%s correct=%s difficulty=%s",
        user_id, skill_id, is_correct, difficulty,
    )
    mastery = _get_or_create_mastery(user_id, skill_id)

    # Update stats
    mastery.total_attempts += 1
    if is_correct:
        mastery.correct_attempts += 1
        mastery.streak += 1
        quality = 4 if difficulty != "hard" else 5
    else:
        mastery.streak = 0
        quality = 1 if difficulty == "easy" else 2

    # Update algorithms
    _update_bkt(mastery, is_correct)
    _update_sm2(mastery, quality)
    _update_mastery_level(mastery)

    # Log the question
    log = QuizQuestionLog(
        user_id=user_id,
        skill_id=skill_id,
        question_text=question_text,
        is_correct=is_correct,
        difficulty=difficulty,
    )
    db.session.add(log)
    db.session.flush()

    logger.info(
        "update_skill_after_answer done: skill_id=%s mastery=%s p_learned=%.3f",
        skill_id, mastery.mastery_level, mastery.p_learned,
    )
    return mastery


def log_chat_topics(user_id: int, text: str):
    """Extract and log topics from a chat message."""
    topics = extract_topics(text)
    for skill_id in topics:
        if skill_id in SKILL_TREE:
            log = ChatTopicLog(user_id=user_id, skill_id=skill_id)
            db.session.add(log)
    if topics:
        db.session.commit()
        logger.info("Logged chat topics for user_id=%s: %s", user_id, topics)
    return topics


def select_quiz_topics(user_id: int, count: int = 5) -> list[dict]:
    """
    Select topics for a quiz using priority:
    1. Topics DUE for review (spaced repetition)
    2. Weak topics (low p_learned)
    3. Topics chatted about but never quizzed
    4. Not-started topics with prerequisites met (ZPD)
    """
    now = datetime.now(timezone.utc)

    # Get all mastery records for this user
    all_mastery = UserSkillMastery.query.filter_by(user_id=user_id).all()
    mastery_map = {m.skill_id: m for m in all_mastery}

    # Get topics the user has chatted about
    chat_topics = db.session.query(ChatTopicLog.skill_id).filter_by(
        user_id=user_id
    ).distinct().all()
    chatted_skills = {t[0] for t in chat_topics}

    # Get mastered skills for ZPD calculation
    mastered_skills = {
        m.skill_id for m in all_mastery
        if m.mastery_level in ("proficient", "mastered")
    }

    selected = []

    # Priority 1: Due for review
    for m in all_mastery:
        if m.next_review_at and m.next_review_at <= now and m.mastery_level != "mastered":
            selected.append({
                "skill_id": m.skill_id,
                "reason": "due_for_review",
                "difficulty": _get_difficulty(m),
            })

    # Priority 2: Weak topics (attempted but low score)
    weak = [m for m in all_mastery if m.p_learned < 0.5 and m.total_attempts > 0]
    weak.sort(key=lambda m: m.p_learned)
    for m in weak:
        if m.skill_id not in {s["skill_id"] for s in selected}:
            selected.append({
                "skill_id": m.skill_id,
                "reason": "weak_topic",
                "difficulty": _get_difficulty(m),
            })

    # Priority 3: Chatted about but never quizzed
    for skill_id in chatted_skills:
        if skill_id not in mastery_map and skill_id not in {s["skill_id"] for s in selected}:
            selected.append({
                "skill_id": skill_id,
                "reason": "chatted_not_quizzed",
                "difficulty": "easy",
            })

    # Priority 4: Not-started topics with prerequisites met (ZPD)
    zpd_ready = get_prerequisites_met(mastered_skills | {"variables", "data_types", "operators"})
    for skill_id in zpd_ready:
        if skill_id not in mastery_map and skill_id not in {s["skill_id"] for s in selected}:
            selected.append({
                "skill_id": skill_id,
                "reason": "zpd_ready",
                "difficulty": "easy",
            })

    # If still not enough, add basic topics
    if len(selected) < count:
        basics = ["variables", "data_types", "strings", "if_else", "for_loop"]
        for skill_id in basics:
            if skill_id not in {s["skill_id"] for s in selected}:
                m = mastery_map.get(skill_id)
                selected.append({
                    "skill_id": skill_id,
                    "reason": "basics",
                    "difficulty": _get_difficulty(m) if m else "easy",
                })

    chosen = selected[:count]
    logger.info(
        "select_quiz_topics: user_id=%s chose %d topic(s): %s",
        user_id, len(chosen), [s["skill_id"] for s in chosen],
    )
    return chosen


def _get_difficulty(mastery: UserSkillMastery | None) -> str:
    """Determine difficulty based on mastery level."""
    if not mastery:
        return "easy"
    level = mastery.mastery_level
    if level in ("not_started", "attempted"):
        return "easy"
    elif level == "familiar":
        return "medium"
    else:
        return "hard"


def get_all_mastery(user_id: int) -> list[dict]:
    """Get all skill mastery data for a user."""
    all_mastery = UserSkillMastery.query.filter_by(user_id=user_id).all()
    mastery_map = {m.skill_id: m.to_dict() for m in all_mastery}

    result = []
    for skill_id, info in SKILL_TREE.items():
        if skill_id in mastery_map:
            entry = mastery_map[skill_id]
        else:
            entry = {
                "skill_id": skill_id,
                "mastery_level": "not_started",
                "p_learned": 0.0,
                "total_attempts": 0,
                "correct_attempts": 0,
                "percentage": 0,
                "streak": 0,
                "next_review_at": None,
            }
        entry["name"] = info["name"]
        entry["category"] = info["category"]
        result.append(entry)

    return result
