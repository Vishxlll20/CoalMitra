from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DocumentWord

router = APIRouter(tags=["insights"])


@router.get("/insights/wordcloud")
def wordcloud(document_id: str | None = None, db: Session = Depends(get_db)):
    from app.services.insight_service import top_words

    q = db.query(DocumentWord)
    if document_id:
        q = q.filter(DocumentWord.document_id == document_id)
    rows = q.all()
    words = top_words([
        {"word": r.word, "count": r.count, "document_id": r.document_id}
        for r in rows
    ])
    # Frontend expects bare WordStat[]: [{word, count}]
    return [{"word": w["word"], "count": w["count"]} for w in words]


@router.get("/insights/topics")
def topics(db: Session = Depends(get_db)):
    from app.models import DocumentTopic, Topic

    rows = (
        db.query(DocumentTopic, Topic)
        .join(Topic, DocumentTopic.topic_id == Topic.id)
        .all()
    )
    # Aggregate by topic: id, key, label, color, weight, quarter, doc_count
    agg: dict[str, dict] = {}
    for dt, t in rows:
        if t.id not in agg:
            agg[t.id] = {
                "id": t.id,
                "key": t.key,
                "label": t.label,
                "color": t.color,
                "weight": 0.0,
                "quarter": dt.quarter or "",
                "doc_count": 0,
            }
        agg[t.id]["weight"] += dt.weight or 0
        agg[t.id]["doc_count"] += 1
    result = sorted(agg.values(), key=lambda x: -x["weight"])
    # Round weights
    for t in result:
        t["weight"] = round(t["weight"], 3)
    return result


@router.get("/insights/topic-drift")
def topic_drift(db: Session = Depends(get_db)):
    from app.models import DocumentTopic, Topic

    rows = (
        db.query(DocumentTopic, Topic)
        .join(Topic, DocumentTopic.topic_id == Topic.id)
        .all()
    )
    # Group by quarter → {quarter, topics: [{key, label, color, weight}]}
    quarter_map: dict[str, dict[str, dict]] = {}
    for dt, t in rows:
        q = dt.quarter or "2024-Q1"
        if q not in quarter_map:
            quarter_map[q] = {}
        if t.key not in quarter_map[q]:
            quarter_map[q][t.key] = {
                "key": t.key,
                "label": t.label,
                "color": t.color,
                "weight": 0.0,
            }
        quarter_map[q][t.key]["weight"] += dt.weight or 0

    result = []
    for q in sorted(quarter_map.keys()):
        topics_list = sorted(quarter_map[q].values(), key=lambda x: -x["weight"])
        for t in topics_list:
            t["weight"] = round(t["weight"], 3)
        result.append({"quarter": q, "topics": topics_list})
    return result


@router.get("/insights/topics/{topic}/documents")
def topic_documents(topic: str, db: Session = Depends(get_db)):
    from app.models import Document, DocumentTopic, Topic

    rows = (
        db.query(Document)
        .join(DocumentTopic, Document.id == DocumentTopic.document_id)
        .join(Topic, Topic.id == DocumentTopic.topic_id)
        .filter(or_(Topic.id == topic, Topic.key == topic, Topic.label.ilike(f"%{topic}%")))
        .all()
    )
    return [
        {
            "id": d.id,
            "title": d.title,
            "block": d.block_name,
            "coalfield": d.coalfield.name if d.coalfield else "",
            "report_date": d.report_date,
        }
        for d in rows
    ]
