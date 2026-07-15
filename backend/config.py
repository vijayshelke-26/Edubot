import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'edu_chatbot.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
    JWT_EXPIRY_HOURS = 24
