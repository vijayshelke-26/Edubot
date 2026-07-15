import logging

from models import db
from models.quiz import QuizQuestion
from models.progress import QuizAttempt, UserProgress

logger = logging.getLogger(__name__)


def _level_to_difficulty(level: str) -> str:
    """Map user level to quiz difficulty."""
    return {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}.get(
        level, "easy"
    )


def get_quiz_questions(user_id: int, domain: str, count: int = 5) -> list[dict]:
    """Get quiz questions at the user's current difficulty level."""
    progress = UserProgress.query.filter_by(user_id=user_id, domain=domain).first()
    level = progress.current_level if progress else "beginner"
    difficulty = _level_to_difficulty(level)

    questions = (
        QuizQuestion.query.filter_by(domain=domain, difficulty=difficulty)
        .order_by(db.func.random())
        .limit(count)
        .all()
    )

    # If not enough questions at this level, supplement with adjacent levels
    if len(questions) < count:
        existing_ids = [q.id for q in questions]
        extra = (
            QuizQuestion.query.filter(
                QuizQuestion.domain == domain,
                ~QuizQuestion.id.in_(existing_ids) if existing_ids else True,
            )
            .order_by(db.func.random())
            .limit(count - len(questions))
            .all()
        )
        questions.extend(extra)

    return {
        "difficulty": difficulty,
        "level": level,
        "questions": [q.to_dict() for q in questions],
    }


def submit_quiz(user_id: int, domain: str, answers: list[dict]) -> dict:
    """Score a quiz submission and update user progress."""
    logger.info("submit_quiz: user_id=%s domain=%s answers=%d", user_id, domain, len(answers))
    score = 0
    total = len(answers)
    results = []

    for ans in answers:
        question = QuizQuestion.query.get(ans["question_id"])
        if not question:
            continue
        is_correct = ans["selected_index"] == question.correct_index
        if is_correct:
            score += 1
        results.append(
            {
                "question_id": question.id,
                "correct": is_correct,
                "correct_index": question.correct_index,
                "explanation": question.explanation,
            }
        )

    # Determine difficulty from the first question
    first_q = QuizQuestion.query.get(answers[0]["question_id"]) if answers else None
    difficulty = first_q.difficulty if first_q else "easy"

    # Record attempt
    attempt = QuizAttempt(
        user_id=user_id,
        domain=domain,
        score=score,
        total=total,
        difficulty=difficulty,
    )
    db.session.add(attempt)

    # Update progress
    progress = UserProgress.query.filter_by(user_id=user_id, domain=domain).first()
    if not progress:
        progress = UserProgress(
            user_id=user_id,
            domain=domain,
            total_quizzes=0,
            total_score=0,
            total_possible=0,
            current_level="beginner",
        )
        db.session.add(progress)

    progress.total_quizzes += 1
    progress.total_score += score
    progress.total_possible += total

    # Recalculate level
    pct = (progress.total_score / progress.total_possible * 100) if progress.total_possible else 0
    if pct >= 80:
        progress.current_level = "advanced"
    elif pct >= 50:
        progress.current_level = "intermediate"
    else:
        progress.current_level = "beginner"

    db.session.commit()

    return {
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total else 0,
        "results": results,
        "new_level": progress.current_level,
    }


def get_quiz_history(user_id: int) -> list[dict]:
    """Get all quiz attempts for a user."""
    logger.info("get_quiz_history: user_id=%s", user_id)
    attempts = (
        QuizAttempt.query.filter_by(user_id=user_id)
        .order_by(QuizAttempt.attempted_at.desc())
        .all()
    )
    return [a.to_dict() for a in attempts]
