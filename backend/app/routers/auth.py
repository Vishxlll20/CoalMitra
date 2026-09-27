from __future__ import annotations

import re
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    SESSION_COOKIE,
    SESSION_DAYS,
    hash_password,
    issue_session,
    token_digest,
    user_for_token,
    user_payload,
    verify_password,
)
from app.core.config import settings
from app.core.database import get_db
from app.models import AuthCredential, AuthSession, Role, User

router = APIRouter(tags=["authentication"])
DEMO_PASSWORD = "CoalMitraDemo2026!"
DEMO_ACCOUNTS = (
    (Role.GEOLOGIST, "geologist@coalmitra.demo", "Dr. Anita Sharma", "Chief Geologist, CMPDIL", "CMPDIL"),
    (Role.MINISTRY_OFFICIAL, "ministry@coalmitra.demo", "Rajesh Iyer", "Director (Coal), MoC", "Ministry of Coal"),
    (Role.AUDITOR, "auditor@coalmitra.demo", "Meera Krishnan", "Senior Auditor, CIL", "CIL"),
)


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class Registration(Credentials):
    password: str = Field(min_length=10, max_length=256)
    name: str = Field(min_length=2, max_length=120)


def _email(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter a valid email address")
    return normalized


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.get("/auth/demo-accounts")
def demo_accounts():
    if not settings.demo_mode:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo accounts are disabled")
    return [
        {"email": email, "password": DEMO_PASSWORD, "role": role.value,
         "name": name, "title": title}
        for role, email, name, title, _ in DEMO_ACCOUNTS
    ]


@router.post("/auth/register")
def register(payload: Registration, response: Response, db: Session = Depends(get_db)):
    email = _email(payload.email)
    if db.query(AuthCredential).filter(AuthCredential.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(name=payload.name.strip(), role=Role.GEOLOGIST, title="Geologist", subsidiary="CMPDIL")
    db.add(user)
    db.flush()
    db.add(AuthCredential(user_id=user.id, email=email, password_hash=hash_password(payload.password)))
    token, _ = issue_session(db, user)
    _set_session_cookie(response, token)
    return user_payload(user) if user else None


@router.post("/auth/login")
def login(payload: Credentials, response: Response, db: Session = Depends(get_db)):
    email = _email(payload.email)
    credential = db.query(AuthCredential).filter(AuthCredential.email == email).first()
    if credential is None or not verify_password(payload.password, credential.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect")
    token, _ = issue_session(db, credential.user)
    _set_session_cookie(response, token)
    return user_payload(credential.user)


@router.get("/auth/me")
def current_session(
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
):
    user = user_for_token(db, token)
    return user_payload(user) if user else None


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
):
    if token:
        session = db.query(AuthSession).filter(AuthSession.token_hash == token_digest(token)).first()
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True,
                           secure=settings.auth_cookie_secure, samesite="lax")


def ensure_demo_accounts() -> None:
    if not settings.demo_mode:
        return
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        for role, email, name, title, subsidiary in DEMO_ACCOUNTS:
            credential = db.query(AuthCredential).filter(AuthCredential.email == email).first()
            if credential:
                continue
            user = db.query(User).filter(User.role == role).first()
            if user is None:
                user = User(name=name, role=role, title=title, subsidiary=subsidiary)
                db.add(user)
                db.flush()
            db.add(AuthCredential(user_id=user.id, email=email, password_hash=hash_password(DEMO_PASSWORD)))
        db.commit()
    finally:
        db.close()