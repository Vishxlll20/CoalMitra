from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central config. Values come from backend/.env (see .env.example)."""

    # Core
    app_name: str = "CoalMitra"
    debug: bool = True

    # Demo flag: 1 = deterministic seeded pipeline (default, zero fragile deps).
    # 0 = real Tesseract / ChromaDB / faster-whisper paths.
    demo_mode: bool = True
    auth_cookie_secure: bool = False

    # Storage roots (relative to the backend package parent)
    storage_dir: str = "storage"
    uploads_dir: str = "storage/uploads"
    pages_dir: str = "storage/pages"
    reports_dir: str = "storage/reports"

    # Database — SQLite fallback if PostgreSQL isn't reachable.
    database_url: str = "postgresql+psycopg2://coalmitra:coalmitra@localhost:5432/coalmitra"

    # Embeddings / RAG
    chroma_dir: str = "chroma"
    embedding_model: str = "intfloat/multilingual-e5-small"

    # LLM (optional real path)
    openai_api_key: str | None = None

    # Whisper (optional real path)
    whisper_model: str = "small"

    # Metrics baseline: manual report prep time in days (used for the headline KPI)
    manual_report_days: float = 28.0

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def model_post_init(self, __context) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        for name in ("storage_dir", "uploads_dir", "pages_dir", "reports_dir"):
            path = Path(getattr(self, name))
            if not path.is_absolute():
                setattr(self, name, str(backend_root / path))


settings = Settings()