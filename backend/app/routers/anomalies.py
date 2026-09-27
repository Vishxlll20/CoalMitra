from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Document
from app.models.report import Anomaly, AnomalyStatus

router = APIRouter(tags=["anomalies"])


def _ser(a: Anomaly) -> dict:
    return {
        "id": a.id,
        "field_key": a.metric_key,
        "field_label": a.label,
        "coalfield_id": a.coalfield_id,
        "block": a.block_name,
        "expected_value": a.expected_value,
        "actual_value": a.actual_value,
        "deviation_pct": a.deviation_pct,
        "severity": a.severity.value if a.severity else "LOW",
        "status": (a.status.value if a.status else "OPEN").lower(),
        "rationale": a.rationale,
        "primary_doc_id": a.document_id,
        "baseline_doc_id": a.baseline_document_id,
        "page_number": a.page_number,
        "bbox": a.bbox or {},
        "confidence": a.confidence or 0,
        "detected_at": a.detected_at.isoformat() if a.detected_at else "",
    }


@router.get("/anomalies")
def list_anomalies(severity: str | None = None, status: str | None = None,
                   coalfield: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Anomaly)
    if severity:
        # Enum column stores uppercase; the frontend may send lowercase.
        q = q.filter(Anomaly.severity == severity.upper())
    if status:
        q = q.filter(Anomaly.status == status.upper())
    if coalfield:
        from app.models import Coalfield
        q = q.join(Coalfield, Anomaly.coalfield_id == Coalfield.id).filter(Coalfield.name == coalfield)
    rows = q.order_by(Anomaly.deviation_pct.desc()).all()
    return [_ser(a) for a in rows]


@router.get("/anomalies/summary")
def anomaly_summary(db: Session = Depends(get_db)):
    from sqlalchemy import func

    rows = (
        db.query(Anomaly.severity, func.count(Anomaly.id))
        .group_by(Anomaly.severity)
        .all()
    )
    counts = {k.value if hasattr(k, "value") else str(k): int(c) for k, c in rows}
    return {
        "total": sum(counts.values()),
        "counts": counts,
    }


@router.post("/anomalies/{anomaly_id}/ack")
def ack_anomaly(anomaly_id: str, db: Session = Depends(get_db)):
    """Mark an anomaly reviewed. Returns the full Anomaly so the UI can swap it
    inline without a refetch."""
    a = db.query(Anomaly).get(anomaly_id)
    if a is None:
        raise HTTPException(404, "Anomaly not found")
    a.status = AnomalyStatus.REVIEWED
    db.add(a)
    db.commit()
    db.refresh(a)
    return _ser(a)


# Backward-compatible alias (some callers use PATCH).
@router.patch("/anomalies/{anomaly_id}/ack")
def ack_anomaly_patch(anomaly_id: str, db: Session = Depends(get_db)):
    return ack_anomaly(anomaly_id, db)