import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.database import create_user, get_user_by_email, get_user_by_id

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def check_password(password: str, stored: str) -> bool:
    salt, h = stored.split("$", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return pyjwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> int:
    try:
        payload = pyjwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (pyjwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> dict | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        user_id = decode_token(auth[7:])
        return get_user_by_id(user_id)
    except HTTPException:
        return None


def require_user(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    if len(password) < 4:
        return JSONResponse(status_code=400, content={"error": "Password must be at least 4 characters"})

    existing = get_user_by_email(email)
    if existing:
        return JSONResponse(status_code=409, content={"error": "Email already registered"})

    user_id = create_user(email, hash_password(password))
    token = create_token(user_id)
    return {"token": token, "user": {"id": user_id, "email": email}}


@router.post("/signin")
async def signin(email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email)
    if not user or not check_password(password, user["password_hash"]):
        return JSONResponse(status_code=401, content={"error": "Invalid email or password"})

    token = create_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"]}}


@router.get("/me")
async def me(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    return {"id": user["id"], "email": user["email"]}
