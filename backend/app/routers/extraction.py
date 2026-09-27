from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Document, DocumentPage, FieldExtraction, TextEmission

router = APIRouter(tags=["extraction"])


@router.get("/documents/{doc_id}/pages")
def get_pages(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).get(doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc_id) \
        .order_by(DocumentPage.page_number).all()
    return [
        {
            "id": p.id,
            "page_number": p.page_number,
            "image_url": f"/static/pages/{doc_id}/{p.page_number}.png",
            "width": p.width,
            "height": p.height,
            "text": p.text,
            "ocr_conf": p.ocr_conf_mean,
        }
        for p in pages
    ]


@router.get("/documents/{doc_id}/fields")
def get_fields(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).get(doc_id)
    if d is None:
        raise HTTPException(404, "Document not found")
    rows = db.query(FieldExtraction).filter(FieldExtraction.document_id == doc_id).all()
    return [
        {
            "id": f.id,
            "field_key": f.field_key,
            "field_label": f.field_label,
            "value": f.value,
            "unit": f.unit,
            "numeric_value": f.numeric_value,
            "confidence": f.confidence,
            "page_number": f.page_number,
            "bbox": f.bbox,
            "matched_text": f.matched_text,
            "method": f.method,
            "doc_id": doc_id,
        }
        for f in rows
    ]


@router.get("/documents/{doc_id}/emissions")
def get_emissions(doc_id: str, page: int | None = None, db: Session = Depends(get_db)):
    query = (
        db.query(TextEmission, DocumentPage.page_number)
        .join(DocumentPage, TextEmission.page_id == DocumentPage.id)
        .filter(TextEmission.document_id == doc_id)
    )
    if page:
        query = query.filter(DocumentPage.page_number == page)
    rows = query.order_by(DocumentPage.page_number, TextEmission.line_no).limit(4000).all()
    return [
        {
            "id": e.id,
            "page_number": pno,
            "text": e.text,
            "bbox": e.bbox,
            "confidence": e.confidence,
            "char_start": e.char_start,
            "char_end": e.char_end,
            "is_heading": bool(e.is_heading),
        }
        for e, pno in rows
    ]


@router.get("/documents/{doc_id}/topics")
def get_topics(doc_id: str, db: Session = Depends(get_db)):
    from app.models import DocumentTopic, Topic
    rows = (
        db.query(DocumentTopic, Topic)
        .join(Topic, DocumentTopic.topic_id == Topic.id)
        .filter(DocumentTopic.document_id == doc_id)
        .all()
    )
    return [
        {"topic": t.label, "weight": dt.weight, "quarter": dt.quarter}
        for dt, t in rows
    ]