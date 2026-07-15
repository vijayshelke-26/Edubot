from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.chat import ChatSession, ChatMessage
from models.quiz import QuizQuestion
from models.progress import QuizAttempt, UserProgress
from models.mastery import UserSkillMastery, ChatTopicLog, QuizQuestionLog
