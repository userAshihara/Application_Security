import re
import pymysql
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, timezone
from security import hash_password, generate_activation_token, hash_token
from db import get_connection
from security import hash_password, generate_activation_token

app = FastAPI(title="User Registration API", description="API for user registration and activation", version="1.0")

ENFORCE_DOMAIN_WHITELIST = False
ALLOWED_DOMAINS = {"student.put.poznan.pl"}

PASSWORD_MIN_LENGTH = 8
BCRYPT_MAX_BYTES = 72

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_check_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Error : These fields cannot be empty")
        return value

    @field_validator("password")
    @classmethod
    def check_password_policy(cls, value: str) -> str:
        errors = []
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            errors.append(f"maximum {BCRYPT_MAX_BYTES} octets")
        if not re.search(r"[a-z]", value):
            errors.append("At least one lowercase letter")
        if not re.search(r"[A-Z]", value):
            errors.append("At least one uppercase letter")
        if not re.search(r"[0-9]", value):
            errors.append("At least one digit")
        if not re.search(r"[^A-Za-z0-9]", value):
            errors.append("At least one special character")
        if errors:
            raise ValueError("Password too weak : " + ", ".join(errors))
        return value

def check_domain(email: str) -> None:
    if not ENFORCE_DOMAIN_WHITELIST:
        return
    domain = email.split("@", 1)[1]
    if domain not in ALLOWED_DOMAINS:
        raise HTTPException(status_code=400, detail="Email domain not authorized")

@app.get("/")
async def root():
    return {
        "message": "User Registration API",
        "endpoints": {
            "/api/register": "POST - Register a new user",
            "/api/activate": "GET  - Activate a user account with a token",
        }
    }

@app.post("/api/register", status_code=201)
def register(data: RegisterRequest):
    email = data.email.lower()
    check_domain(email)

    password_hash = hash_password(data.password)
    token, token_hash, expires_at = generate_activation_token()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users
                    (first_name, last_name, email, password_hash,
                     is_active, activation_token_hash, token_expires_at)
                VALUES (%s, %s, %s, %s, FALSE, %s, %s)
                """,
                (
                    data.first_name,
                    data.last_name,
                    email,
                    password_hash,
                    token_hash,
                    expires_at.replace(tzinfo=None),
                ),
            )
        conn.commit()
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        if e.args[0] == 1062 and "'email'" in str(e.args[1]):
            raise HTTPException(status_code=409, detail="Email already in use")
        raise
    finally:
        conn.close()

    # Send email (from the console)
    activation_link = f"http://localhost:8000/api/activate?token={token}"
    print("=" * 60)
    print("Activation link (simulation) :", activation_link)
    print("=" * 60)

    return {"message": "Account created. Check the server console for the activation link."}

@app.get("/api/activate")
def activate(token: str = Query(min_length=20, max_length=100)):
    token_hash = hash_token(token)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, token_expires_at
                FROM users
                WHERE activation_token_hash = %s
                """,
                (token_hash,),
            )
            user = cursor.fetchone()

            if user is None:
                raise HTTPException(status_code=400, detail="Invalid activation link")

            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if user["token_expires_at"] is None or user["token_expires_at"] < now_utc:
                raise HTTPException(status_code=410, detail="Activation link expired")

            cursor.execute(
                """
                UPDATE users
                SET is_active = TRUE,
                    activation_token_hash = NULL,
                    token_expires_at = NULL
                WHERE id = %s AND activation_token_hash = %s
                """,
                (user["id"], token_hash),
            )
            if cursor.rowcount != 1:
                raise HTTPException(status_code=400, detail="Invalid activation link")

        conn.commit()
    finally:
        conn.close()

    return {"message": "Account activated. You can now log in."}