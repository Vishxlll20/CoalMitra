from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.core.auth import require_roles
from app.core.database import get_db
from app.models import Document, DocCategory, DocSource, DocStatus, FieldExtraction, Role

router = APIRouter(tags=["documents"])

CATEGORY_MAP = {
    "PROSPECTING": DocCategory.PROSPECTING,
    "GEOLOGICAL_REPORT": DocCategory.GEOLOGICAL_REPORT,
    "PRODUCTION": DocCategory.PRODUCTION,
    "ENVIRONMENTAL": DocCategory.ENVIRONMENTAL,
    "RESERVES": DocCategory.RESERVES,
}


def _doc_payload(d: Document, fields_count: int = 0) -> dict:
    c = d.coalfield
    return {
        "id": d.id,
        "title": d.title,
        "category": d.category.value if d.category else "GEOLOGICAL_REPORT",
        "coalfield_id": d.coalfield_id or "",
        "coalfield_name": c.name if c else "",
        "block": d.block_name or "",
        "district": d.district or "",
        "source_type": d.source_type.value if d.source_type else "PDF",
        "status": d.status.value if d.status else "UPLOADING",
        "ingestion_progress": d.ingestion_progress or {"step": "UPLOADING", "pct": 0, "message": ""},
        "page_count": d.page_count or 0,
        "size_bytes": d.size_bytes or 0,
        "total_confidence": d.total_confidence or 0,
        "report_date": d.report_date or "",
        "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else "",
        "pages_dir": d.pages_dir or "",
    }


@router.get("/documents")
def list_documents(category: str | None = None, coalfield: str | None = None,
                   status: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if category:
        query = query.filter(Document.category == CATEGORY_MAP.get(category))
    if coalfield:
        from app.models import Coalfield
        query = query.join(Coalfield, Document.coalfield_id == Coalfield.id).filter(Coalfield.name == coalfield)
    if status:
        query = query.filter(Document.status == status)
    if q:
        query = query.filter(or_(
            Document.title.ilike(f"%{q}%"),
            Document.block_name.ilike(f"%{q}%"),
        ))
    docs = query.order_by(Document.uploaded_at.desc()).all()
    return [_doc_payload(d) for d in docs]


@router.get("/documents/coalfields")
def list_coalfields(db: Session = Depends(get_db)):
    from app.models import Coalfield
    return [
        {"id": c.id, "name": c.name, "subsidiary": c.subsidiary, "state": c.state,
         "area_sqkm": getattr(c, "area_sqkm", 0) or 0,
         "baseline_gcv": getattr(c, "baseline_gcv", 0) or 0,
         "baseline_ash": getattr(c, "baseline_ash", 0) or 0,
         "baseline_ob_ratio": getattr(c, "baseline_ob_ratio", 0) or 0,
         "reserve_mt": getattr(c, "reserve_mt", 0) or 0}
        for c in db.query(Coalfield).all()
    ]


@router.get("/documents/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).get(doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    n = db.query(FieldExtraction).filter(FieldExtraction.document_id == d.id).count()
    return _doc_payload(d, n)


@router.get("/documents/{doc_id}/status")
def doc_status(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).get(doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    return {
        "document_id": d.id,
        "status": d.status.value if d.status else "UPLOADING",
        "step": (d.ingestion_progress or {}).get("step", ""),
        "pct": (d.ingestion_progress or {}).get("pct", 0),
        "message": (d.ingestion_progress or {}).get("message", ""),
    }


@router.get("/documents/{doc_id}/progress")
def doc_progress(doc_id: str, db: Session = Depends(get_db)):
    """Legacy alias."""
    return doc_status(doc_id, db)


def _run_ingest(doc_id: str):
    from app.services.ingestion import ingest_document
    ingest_document(doc_id)


@router.post("/documents/upload", dependencies=[Depends(require_roles(Role.GEOLOGIST))])
async def upload_documents(
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    title: str | None = None,
    category: str = "GEOLOGICAL_REPORT",
    as_user: str = "GEOLOGIST",
    db: Session = Depends(get_db),
):
    upload_root = Path(settings.uploads_dir)
    upload_root.mkdir(parents=True, exist_ok=True)

    created = []
    for f in files:
        name = Path(f.filename or "doc.pdf").name
        dest = upload_root / f"{name}-{uuid.uuid4().hex[:8]}.pdf"
        content = await f.read()
        dest.write_bytes(content)
        doc = Document(
            title=title or name,
            category=CATEGORY_MAP.get(category, DocCategory.GEOLOGICAL_REPORT),
            source_type=DocSource.PDF,
            status=DocStatus.UPLOADING,
            size_bytes=len(content),
            file_path=str(dest),
            ingestion_progress={"step": "UPLOADING", "pct": 5, "message": "Queued"},
        )
        db.add(doc)
        db.flush()
        created.append(doc)
        db.commit()
        background.add_task(_run_ingest, doc.id)

    # Frontend expects bare Document[]
    return [_doc_payload(d) for d in created]


@router.get("/documents/{doc_id}/file")
def doc_file(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).get(doc_id)
    if d is None or not d.file_path:
        raise HTTPException(404, "Source file unavailable")
    file_path = Path(d.file_path)
    if not file_path.is_absolute():
        file_path = Path(__file__).resolve().parents[2] / file_path
    if not file_path.is_file():
        raise HTTPException(404, "Source file unavailable")
    from fastapi.responses import FileResponse
    return FileResponse(file_path, filename=f"{d.title or 'doc'}.pdf")


@router.delete("/documents/{doc_id}", dependencies=[Depends(require_roles(Role.GEOLOGIST))])
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).get(doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    db.delete(d)
    db.commit()
    return {"ok": True, "id": doc_id}
