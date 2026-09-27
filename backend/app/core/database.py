from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def _resolve_storage(username: str) -> str:
    """If a SQLite fallback is used, put the file inside backend (not CWD)."""
    if username.startswith("sqlite"):
        root = Path(__file__).resolve().parents[2]
        return f"sqlite:///{root / 'coalmitra.db'}"
    return username


DATABASE_URL = _resolve_storage(settings.database_url)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=settings.debug and False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import app.models  # noqa: F401 — registers all tables
    Base.metadata.create_all(bind=engine)


def json_type():
    """Return the right JSON column type for the active backend."""
    from sqlalchemy.dialects.postgresql import JSONB
    if DATABASE_URL.startswith("postgres"):
        return JSONB
    from sqlalchemy import JSON
    return JSON