import logging
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from config import Config

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=Config.JWT_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
    logger.info("Issued JWT for user_id=%s", user_id)
    return token


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.warning("Rejected JWT: %s", e.__class__.__name__)
        return None
