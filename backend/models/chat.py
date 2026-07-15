from datetime import datetime, timezone
from models import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    messages = db.relationship(
        "ChatMessage", backref="session", lazy=True, order_by="ChatMessage.created_at"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "message_count": len(self.messages),
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False
    )
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    detected_domain = db.Column(db.String(50))
    detected_intent = db.Column(db.String(50))
    complexity_level = db.Column(db.String(20))
    feedback = db.Column(db.Integer)  # 1 = thumbs up, -1 = thumbs down, NULL = none
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "detected_domain": self.detected_domain,
            "detected_intent": self.detected_intent,
            "complexity_level": self.complexity_level,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat(),
        }
