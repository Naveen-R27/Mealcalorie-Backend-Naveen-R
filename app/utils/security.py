from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def _safe_truncate_password(password: str) -> str:
    b = password.encode("utf-8")
    if len(b) > 72:

        truncated = b[:72]
        try:
            return truncated.decode("utf-8")
        except UnicodeDecodeError:

            return truncated.decode("utf-8", errors="ignore")
    return password

def hash_password(password: str) -> str:
    password = _safe_truncate_password(password)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = _safe_truncate_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
