from datetime import datetime, timezone
from models import db


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    domain = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "domain": self.domain,
            "score": self.score,
            "total": self.total,
            "difficulty": self.difficulty,
            "attempted_at": self.attempted_at.isoformat(),
        }


class UserProgress(db.Model):
    __tablename__ = "user_progress"
    __table_args__ = (
        db.UniqueConstraint("user_id", "domain", name="uq_user_domain"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    domain = db.Column(db.String(50), nullable=False)
    total_quizzes = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    total_possible = db.Column(db.Integer, default=0)
    current_level = db.Column(db.String(20), default="beginner")

    def to_dict(self):
        pct = (self.total_score / self.total_possible * 100) if self.total_possible else 0
        return {
            "id": self.id,
            "user_id": self.user_id,
            "domain": self.domain,
            "total_quizzes": self.total_quizzes,
            "total_score": self.total_score,
            "total_possible": self.total_possible,
            "current_level": self.current_level,
            "percentage": round(pct, 1),
        }
