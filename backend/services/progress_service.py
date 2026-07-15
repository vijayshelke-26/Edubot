import logging

from models.progress import UserProgress, QuizAttempt

logger = logging.getLogger(__name__)

DOMAINS = ["programming"]


def get_summary(user_id: int) -> dict:
    """Get progress summary across all domains."""
    logger.info("get_summary: user_id=%s", user_id)
    progress_list = UserProgress.query.filter_by(user_id=user_id).all()
    progress_map = {p.domain: p.to_dict() for p in progress_list}

    summary = []
    for domain in DOMAINS:
        if domain in progress_map:
            summary.append(progress_map[domain])
        else:
            summary.append(
                {
                    "domain": domain,
                    "total_quizzes": 0,
                    "total_score": 0,
                    "total_possible": 0,
                    "current_level": "beginner",
                    "percentage": 0,
                }
            )

    total_quizzes = sum(s["total_quizzes"] for s in summary)
    total_score = sum(s["total_score"] for s in summary)
    total_possible = sum(s["total_possible"] for s in summary)
    overall_pct = (total_score / total_possible * 100) if total_possible else 0

    return {
        "domains": summary,
        "overall": {
            "total_quizzes": total_quizzes,
            "total_score": total_score,
            "total_possible": total_possible,
            "percentage": round(overall_pct, 1),
        },
    }


def get_domain_detail(user_id: int, domain: str) -> dict:
    """Get detailed progress for a specific domain."""
    logger.info("get_domain_detail: user_id=%s domain=%s", user_id, domain)
    progress = UserProgress.query.filter_by(user_id=user_id, domain=domain).first()

    attempts = (
        QuizAttempt.query.filter_by(user_id=user_id, domain=domain)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
        .all()
    )

    return {
        "progress": progress.to_dict() if progress else {
            "domain": domain,
            "total_quizzes": 0,
            "total_score": 0,
            "total_possible": 0,
            "current_level": "beginner",
            "percentage": 0,
        },
        "recent_attempts": [a.to_dict() for a in attempts],
    }
