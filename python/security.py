import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

TOKEN_VALIDITY = timedelta(hours=24)

def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")

def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )

def generate_activation_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + TOKEN_VALIDITY
    return token, token_hash, expires_at


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()