"""
Adaptive quiz service: generates personalized quizzes using Gemini LLM
based on user's learning history and spaced repetition schedule.
"""

import json
import logging
import time
from models import db
from models.quiz import QuizQuestion
from models.progress import QuizAttempt, UserProgress
from nlp.skill_tree import SKILL_TREE
from services.mastery_service import (
    select_quiz_topics, update_skill_after_answer, get_all_mastery
)

logger = logging.getLogger(__name__)


def _generate_questions_llm(topics: list[dict]) -> list[dict]:
    """Generate quiz questions using Gemini LLM."""
    from nlp.llm_generator import is_available

    if not is_available():
        return []

    from nlp.llm_generator import _client

    topic_descriptions = []
    for t in topics:
        skill_info = SKILL_TREE.get(t["skill_id"], {})
        name = skill_info.get("name", t["skill_id"])
        diff = t["difficulty"]
        topic_descriptions.append(f"- Topic: {name}, Difficulty: {diff}")

    topics_text = "\n".join(topic_descriptions)

    prompt = f"""Generate exactly {len(topics)} multiple-choice programming quiz questions in JSON format.

Topics and difficulty levels:
{topics_text}

Difficulty guide:
- easy: Test basic recall and understanding. Simple, direct questions.
- medium: Test application and understanding. Requires thinking.
- hard: Test analysis and evaluation. Tricky edge cases, deeper understanding.

Return ONLY a JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "skill_id": "the_skill_id",
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Why the correct answer is correct",
    "difficulty": "easy"
  }}
]

Rules:
- Generate exactly one question per topic in the order given
- Each question must have exactly 4 options
- correct_index is 0-based (0, 1, 2, or 3)
- Make questions about Python programming
- Questions should be educational and clear
- Explanations should teach, not just state the answer
- Use the skill_id values: {[t['skill_id'] for t in topics]}"""

    for attempt in range(2):
        try:
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and response.text:
                text = response.text.strip()
                # Remove markdown code fences if present
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                    text = text.rsplit("```", 1)[0]
                questions = json.loads(text)
                if isinstance(questions, list) and len(questions) > 0:
                    return questions
        except json.JSONDecodeError as e:
            logger.warning("Quiz LLM JSON parse error: %s", e)
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                time.sleep(5)
                continue
            logger.error("Quiz LLM generation failed: %s", e)
            break

    return []


def _get_fallback_questions(topics: list[dict]) -> list[dict]:
    """Fallback: get questions from the static quiz bank."""
    questions = []
    for t in topics:
        difficulty = t["difficulty"]
        q = (
            QuizQuestion.query
            .filter_by(domain="programming", difficulty=difficulty)
            .order_by(db.func.random())
            .first()
        )
        if q:
            questions.append({
                "id": q.id,
                "skill_id": t["skill_id"],
                "question": q.question,
                "options": q.options,
                "correct_index": q.correct_index,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "source": "static",
            })
    return questions


def start_adaptive_quiz(user_id: int) -> dict:
    """Generate a personalized quiz based on user's learning state."""
    logger.info("start_adaptive_quiz: user_id=%s", user_id)
    # Select topics
    topics = select_quiz_topics(user_id, count=5)

    # Try LLM generation
    questions = _generate_questions_llm(topics)

    if questions:
        # Add skill_id from topics if missing
        for i, q in enumerate(questions):
            if "skill_id" not in q and i < len(topics):
                q["skill_id"] = topics[i]["skill_id"]
            q["source"] = "generated"
            q["id"] = f"gen_{i}"
    else:
        # Fallback to static questions
        questions = _get_fallback_questions(topics)

    # Add skill names
    for q in questions:
        skill_info = SKILL_TREE.get(q.get("skill_id", ""), {})
        q["skill_name"] = skill_info.get("name", q.get("skill_id", "Programming"))

    source = questions[0].get("source") if questions else None
    logger.info(
        "start_adaptive_quiz done: user_id=%s returned %d question(s) (source=%s)",
        user_id, len(questions), source,
    )
    return {
        "questions": questions,
        "topics": [
            {
                "skill_id": t["skill_id"],
                "name": SKILL_TREE.get(t["skill_id"], {}).get("name", t["skill_id"]),
                "reason": t["reason"],
                "difficulty": t["difficulty"],
            }
            for t in topics
        ],
    }


def submit_adaptive_quiz(user_id: int, answers: list[dict]) -> dict:
    """
    Score an adaptive quiz and update all mastery models.
    answers: [{"skill_id": "...", "question_text": "...", "selected_index": 0, "correct_index": 1, "difficulty": "easy"}, ...]
    """
    logger.info("submit_adaptive_quiz: user_id=%s answers=%d", user_id, len(answers))
    score = 0
    total = len(answers)
    results = []

    for ans in answers:
        is_correct = ans["selected_index"] == ans["correct_index"]
        if is_correct:
            score += 1

        skill_id = ans.get("skill_id", "variables")
        difficulty = ans.get("difficulty", "easy")
        question_text = ans.get("question_text", "")

        # Update SM-2 + BKT + mastery level
        mastery = update_skill_after_answer(
            user_id, skill_id, is_correct, question_text, difficulty
        )

        results.append({
            "skill_id": skill_id,
            "skill_name": SKILL_TREE.get(skill_id, {}).get("name", skill_id),
            "correct": is_correct,
            "correct_index": ans["correct_index"],
            "explanation": ans.get("explanation", ""),
            "new_mastery": mastery.mastery_level,
            "p_learned": round(mastery.p_learned, 3),
        })

    # Also update the old UserProgress for backward compatibility
    progress = UserProgress.query.filter_by(user_id=user_id, domain="programming").first()
    if not progress:
        progress = UserProgress(
            user_id=user_id, domain="programming",
            total_quizzes=0, total_score=0, total_possible=0,
            current_level="beginner",
        )
        db.session.add(progress)

    progress.total_quizzes += 1
    progress.total_score += score
    progress.total_possible += total

    pct = (progress.total_score / progress.total_possible * 100) if progress.total_possible else 0
    if pct >= 80:
        progress.current_level = "advanced"
    elif pct >= 50:
        progress.current_level = "intermediate"
    else:
        progress.current_level = "beginner"

    # Record attempt
    attempt = QuizAttempt(
        user_id=user_id, domain="programming",
        score=score, total=total, difficulty="adaptive",
    )
    db.session.add(attempt)
    db.session.commit()

    logger.info(
        "submit_adaptive_quiz done: user_id=%s score=%d/%d new_level=%s",
        user_id, score, total, progress.current_level,
    )
    return {
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total else 0,
        "results": results,
        "new_level": progress.current_level,
    }
