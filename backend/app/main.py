from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage dirs exist
for d in (settings.uploads_dir, settings.pages_dir, settings.reports_dir):
    Path(d).mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def _startup():
    try:
        init_db()
    except Exception as exc:  # surfaced loudly for the demo
        import logging
        logging.getLogger("coalmitra").error(f"DB init failed: {exc}")
        return
    # Auto-seed an empty database so a fresh checkout demos immediately
    # (idempotent — no-ops when the corpus already exists).
    try:
        from app.core.database import SessionLocal
        from app.models import Document
        from sqlalchemy import func

        db = SessionLocal()
        try:
            has_docs = (db.query(func.count(Document.id)).scalar() or 0) > 0
        finally:
            db.close()
        if not has_docs:
            from app.seed.run_seed import run
            run()
    except Exception as exc:  # never block boot on seed failure
        import logging
        logging.getLogger("coalmitra").error(f"Auto-seed failed: {exc}")


# Static mounts for rendered pages / uploaded PDFs / exported reports
app.mount("/static/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
app.mount("/static/pages", StaticFiles(directory=settings.pages_dir), name="pages")
app.mount("/static/reports", StaticFiles(directory=settings.reports_dir), name="reports")


@app.get("/api/health")
def health():
    from app.core.config import settings as s
    from app.core.database import SessionLocal
    from app.models import Document
    from sqlalchemy import func

    db = SessionLocal()
    try:
        doc_count = db.query(func.count(Document.id)).scalar() or 0
    finally:
        db.close()
    return {
        "status": "ok",
        "demo_mode": s.demo_mode,
        "documents": doc_count,
        "database": "sqlite" if "sqlite" in s.database_url else "postgresql",
    }


@app.get("/api/seed-state")
def seed_state():
    """Tells the frontend whether the corpus is seeded (warn if not)."""
    from app.core.database import SessionLocal
    from app.models import Document, Topic
    from sqlalchemy import func

    db = SessionLocal()
    try:
        docs = db.query(func.count(Document.id)).scalar() or 0
        topics = db.query(func.count(Topic.id)).scalar() or 0
        chroma_count = 0
        try:
            from app.services.index_service import search
            chroma_count = search.collection_count()
        except Exception:
            pass
        return {
            "documents": docs,
            "topics": topics,
            "chroma_chunks": chroma_count,
            "seeded": docs > 0,
        }
    finally:
        db.close()


# Routers are mounted in a function so imports resolve after services exist.
def _mount_routers():
    from app.routers import (
        anomalies,
        chat,
        dashboard,
        documents,
        extraction,
        insights,
        metrics,
        reports,
    )

    for r in (documents, extraction, reports, insights, anomalies, chat, metrics, dashboard):
        app.include_router(r.router, prefix="/api")


_mount_routers()