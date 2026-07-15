import json
import logging
import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect, text
from config import Config
from models import db, QuizQuestion

logger = logging.getLogger(__name__)


def configure_logging():
    """
    Set up Python's standard logging once, at application startup.

    A single StreamHandler on the root logger means every module logger
    (services, NLP) propagates here with a consistent format, without the
    route or persistence layers having to know anything about logging.
    Verbosity is controlled by the LOG_LEVEL environment variable.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(h, "_edubot_handler", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", "%H:%M:%S")
        )
        handler._edubot_handler = True
        root.addHandler(handler)


def seed_quiz_questions(app):
    """Load quiz questions from JSON files into the database if empty."""
    with app.app_context():
        if QuizQuestion.query.first():
            return  # Already seeded

        quiz_dir = os.path.join(os.path.dirname(__file__), "data", "quizzes")
        if not os.path.exists(quiz_dir):
            return

        count = 0
        for filename in os.listdir(quiz_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(quiz_dir, filename)
            with open(filepath) as f:
                questions = json.load(f)
            for q in questions:
                qq = QuizQuestion(
                    domain=q["domain"],
                    difficulty=q["difficulty"],
                    question=q["question"],
                    options=q["options"],
                    correct_index=q["correct_index"],
                    explanation=q.get("explanation", ""),
                )
                db.session.add(qq)
                count += 1

        db.session.commit()
        logger.info("Seeded %d quiz questions.", count)


def run_lightweight_migrations(app):
    """Add columns added after the initial schema. Idempotent."""
    with app.app_context():
        inspector = inspect(db.engine)
        if "chat_messages" not in inspector.get_table_names():
            return
        cols = {c["name"] for c in inspector.get_columns("chat_messages")}
        if "feedback" not in cols:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE chat_messages ADD COLUMN feedback INTEGER"))
            logger.info("Migration: added chat_messages.feedback column")


def create_app():
    configure_logging()
    app = Flask(__name__)
    app.config.from_object(Config)
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    origins = [o.strip() for o in cors_origins.split(",")] if cors_origins != "*" else "*"
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

    db.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.chat import chat_bp
    from routes.quiz import quiz_bp
    from routes.progress import progress_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(progress_bp)

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        run_lightweight_migrations(app)
        seed_quiz_questions(app)

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error"}, 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
