from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models import Document, DocumentPage, FieldExtraction, QuantMetric, Role, TextEmission, User
from app.models.chat import AuditEvent
from app.models.report import Anomaly, AnomalyStatus
from app.utils.text import num

router = APIRouter(tags=["extraction"])


class FieldCorrection(BaseModel):
    value: str = Field(min_length=1, max_length=120)


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


@router.get("/documents/{doc_id}/fields", dependencies=[Depends(require_roles(Role.GEOLOGIST, Role.AUDITOR))])
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


@router.patch("/documents/{doc_id}/fields/{field_id}", dependencies=[Depends(require_roles(Role.GEOLOGIST))])
def correct_field(
    doc_id: str,
    field_id: str,
    payload: FieldCorrection,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    field = (
        db.query(FieldExtraction)
        .filter(FieldExtraction.id == field_id, FieldExtraction.document_id == doc_id)
        .first()
    )
    if field is None:
        raise HTTPException(404, "Extracted field not found")
    value = payload.value.strip()
    if not value:
        raise HTTPException(422, "Corrected value cannot be empty")

    previous_value = field.value
    field.value = value
    field.numeric_value = num(value)
    field.confidence = 1.0
    field.method = "human"
    metrics = (
        db.query(QuantMetric)
        .filter(QuantMetric.document_id == doc_id, QuantMetric.metric_key == field.field_key)
        .all()
    )
    for metric in metrics:
        if field.numeric_value is not None:
            metric.value = field.numeric_value
            metric.conf = 1.0
    document = db.query(Document).get(doc_id)
    if document:
        document.total_confidence = db.query(func.avg(FieldExtraction.confidence)).filter(
            FieldExtraction.document_id == doc_id
        ).scalar() or 0
    db.add(AuditEvent(
        actor_role=user.role.value,
        action="corrected_field",
        subject=json.dumps({
            "document_id": doc_id,
            "field_id": field_id,
            "field_key": field.field_key,
            "previous_value": previous_value,
            "corrected_value": value,
        }),
    ))
    db.commit()
    db.refresh(field)

    db.query(Anomaly).filter(
        Anomaly.document_id == doc_id,
        Anomaly.status == AnomalyStatus.OPEN,
    ).delete(synchronize_session=False)
    db.commit()

    from app.services.ingestion import _assign_topics_and_detect_anomalies, create_report
    _assign_topics_and_detect_anomalies(db, doc_id)
    create_report(doc_id)
    return {
        "id": field.id,
        "field_key": field.field_key,
        "field_label": field.field_label,
        "value": field.value,
        "unit": field.unit,
        "numeric_value": field.numeric_value,
        "confidence": field.confidence,
        "page_number": field.page_number,
        "bbox": field.bbox,
        "matched_text": field.matched_text,
        "method": field.method,
        "doc_id": doc_id,
    }


@router.get("/documents/{doc_id}/emissions", dependencies=[Depends(require_roles(Role.GEOLOGIST, Role.AUDITOR))])
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