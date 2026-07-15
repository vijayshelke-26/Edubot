from models import db


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # list of 4 strings
    correct_index = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text)

    def to_dict(self, include_answer=False):
        d = {
            "id": self.id,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "question": self.question,
            "options": self.options,
        }
        if include_answer:
            d["correct_index"] = self.correct_index
            d["explanation"] = self.explanation
        return d
