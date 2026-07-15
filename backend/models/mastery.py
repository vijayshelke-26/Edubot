from datetime import datetime, timezone
from models import db


class UserSkillMastery(db.Model):
    """Tracks per-user, per-skill mastery using SM-2 + BKT."""
    __tablename__ = "user_skill_mastery"
    __table_args__ = (
        db.UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.String(50), nullable=False)

    # Khan-style mastery level
    mastery_level = db.Column(db.String(20), default="not_started")

    # BKT: probability the student has learned this skill (0.0 to 1.0)
    p_learned = db.Column(db.Float, default=0.0)

    # SM-2: spaced repetition parameters
    easiness_factor = db.Column(db.Float, default=2.5)
    interval_days = db.Column(db.Integer, default=0)
    repetitions = db.Column(db.Integer, default=0)
    next_review_at = db.Column(db.DateTime, nullable=True)

    # Stats
    total_attempts = db.Column(db.Integer, default=0)
    correct_attempts = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        pct = (self.correct_attempts / self.total_attempts * 100) if self.total_attempts else 0
        return {
            "skill_id": self.skill_id,
            "mastery_level": self.mastery_level,
            "p_learned": round(self.p_learned, 3),
            "total_attempts": self.total_attempts,
            "correct_attempts": self.correct_attempts,
            "percentage": round(pct, 1),
            "streak": self.streak,
            "next_review_at": self.next_review_at.isoformat() if self.next_review_at else None,
        }


class ChatTopicLog(db.Model):
    """Tracks which topics a user asks about in chat."""
    __tablename__ = "chat_topic_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class QuizQuestionLog(db.Model):
    """Logs every quiz question attempt for analytics."""
    __tablename__ = "quiz_question_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
