from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.auth import require_roles
from app.core.database import get_db
from app.models import Document, FieldExtraction, QuantMetric, Role
from app.models.report import Report, ReportStatus

router = APIRouter(tags=["reports"])


def _section_ser(sec: dict, doc_id: str) -> dict:
    """Serialize one stored section into the frontend ReportSection shape.

    Stored sections carry `body` (paragraph list) or `table` ({headers, rows});
    the frontend expects a single `content` object of the same shape, plus refs.
    """
    body = sec.get("body", [])
    table = sec.get("table")
    content: dict = {}
    if table is not None:
        content = {"headers": table.get("headers", []), "rows": table.get("rows", [])}
    else:
        content = {"paragraphs": body if isinstance(body, list) else [str(body)]}
    return {
        "kind": sec.get("kind"),
        "title": sec.get("title"),
        "content": content,
        "refs": [
            {
                **r,
                "document_id": r.get("document_id") or doc_id,
            }
            for r in sec.get("refs", [])
        ],
    }


def _report_ser(r: Report, db: Session) -> dict:
    """Full Report payload the frontend type expects."""
    doc = db.query(Document).get(r.document_id)
    sections = [_section_ser(s, r.document_id) for s in (r.sections or [])]
    total_refs = sum(len(s.get("refs", [])) for s in sections)
    summary = (r.narrative or {}).get("summary") or ""
    if not summary and sections:
        paras = sections[0]["content"].get("paragraphs") or []
        summary = paras[0] if paras else ""
    return {
        "id": r.id,
        "title": r.title,
        "document_id": r.document_id,
        "document_title": doc.title if doc else "",
        "block": doc.block_name if doc else "",
        "coalfield": doc.coalfield.name if doc and doc.coalfield else "",
        "role": getattr(r, "role", "GEOLOGIST") or "GEOLOGIST",
        "summary": summary,
        "status": r.status.value,
        "generated_at": r.generated_at.isoformat() if r.generated_at else "",
        "sections": sections,
        "total_refs": total_refs,
        "source_count": r.source_count,
    }


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    rows = db.query(Report).order_by(Report.generated_at.desc()).all()
    return [_report_ser(r, db) for r in rows]


@router.get("/reports/{report_id}")
def get_report_by_id(report_id: str, db: Session = Depends(get_db)):
    r = db.query(Report).get(report_id)
    if r is None:
        raise HTTPException(404, "Report not found")
    return _report_ser(r, db)


@router.get("/documents/{doc_id}/report")
def get_report(doc_id: str, db: Session = Depends(get_db)):
    r = (
        db.query(Report)
        .filter(Report.document_id == doc_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if r is None:
        return {"exists": False}
    return _report_ser(r, db)


@router.post("/reports/generate", dependencies=[Depends(require_roles(Role.GEOLOGIST))])
def generate_report(payload: dict | None = None, db: Session = Depends(get_db)):
    """Auto-generate a report. Optionally scoped to a document_id; otherwise the
    latest READY document is used (the demo's one-click generate)."""
    from app.services.ingestion import create_report

    doc_id = (payload or {}).get("document_id")
    if not doc_id:
        doc = (
            db.query(Document)
            .filter(Document.block_name.isnot(None))
            .order_by(Document.uploaded_at.desc())
            .first()
        )
        if doc is None:
            raise HTTPException(400, "No documents available to report on")
        doc_id = doc.id

    created = create_report(doc_id)
    if created is None:
        raise HTTPException(400, "Cannot generate report for this document")
    # Re-fetch in the request's session (create_report uses its own SessionLocal)
    r = (
        db.query(Report)
        .filter(Report.document_id == doc_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if r is None:
        raise HTTPException(500, "Report was created but could not be fetched")
    return _report_ser(r, db)


@router.post("/documents/{doc_id}/report/generate", dependencies=[Depends(require_roles(Role.GEOLOGIST))])
def generate_document_report(doc_id: str, db: Session = Depends(get_db)):
    from app.services.ingestion import create_report
    created = create_report(doc_id)
    if created is None:
        raise HTTPException(400, "Cannot generate report for this document")
    r = (
        db.query(Report)
        .filter(Report.document_id == doc_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if r is None:
        raise HTTPException(500, "Report was created but could not be fetched")
    return _report_ser(r, db)


@router.get("/reports/{report_id}/export.pdf")
def export_report_pdf(report_id: str, db: Session = Depends(get_db)):
    r = db.query(Report).get(report_id)
    if r is None:
        raise HTTPException(404, "Report not found")
    from fastapi.responses import FileResponse

    out_path = str(Path(settings.reports_dir) / f"{report_id}.pdf")
    if not r.pdf_path or not Path(r.pdf_path).exists():
        from app.services.report_service import render_report_pdf
        render_report_pdf(r.title, r.sections or [], out_path)
        r.pdf_path = out_path
        db.add(r)
        db.commit()
    return FileResponse(out_path, filename=f"{Path(r.title).stem or 'report'}.pdf",
                        media_type="application/pdf")


@router.get("/reports/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    """Legacy alias kept for compatibility."""
    return export_report_pdf(report_id, db)