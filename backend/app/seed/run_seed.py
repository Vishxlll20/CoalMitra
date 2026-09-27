"""Seeding — idempotent corpus builder.

Drops + recreates all tables, then authors 18 realistic coal documents that
flow through the REAL ingestion pipeline (pdf_service → text_emissions →
extraction_service → reports → anomalies → word stats → vector index), plus
users, coalfield baselines, topics, metric snapshots, chat history and audit
events. Everything the demo screens need is present after one run.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.models import (  # noqa: E402
    Coalfield,
    DocumentPage,
    DocumentWord,
    DocCategory,
    DocSource,
    DocStatus,
    FieldExtraction,
    QuantMetric,
    Role,
    TextEmission,
    Topic,
    User,
)
from app.models.chat import (
    AuditEvent,
    ChatCitation,
    ChatMessage,
    ChatRole,
    ChatSession,
)
from app.models.metric import MetricSnapshot
from app.models.report import Anomaly, Report, ReportStatus
from app.models.document import Document
from app.models.topic import DocumentTopic

# Ensure storage exists
from app.seed.coalfield_data import BLOCKS, COALFIELDS, SEAMS


def _wipe():
    import os
    Base.metadata.drop_all(bind=engine)
    init_db()
    for d in (settings.uploads_dir, settings.pages_dir, settings.reports_dir):
        os.makedirs(d, exist_ok=True)


def _mk_topics(db):
    topics = [
        Topic(key="exploration", label="Exploration", color="#E8A33D"),
        Topic(key="reserves", label="Reserves", color="#C0392B"),
        Topic(key="seam-quality", label="Seam Quality", color="#5E9EDB"),
        Topic(key="environment", label="Environment", color="#46A758"),
        Topic(key="production", label="Production", color="#6D6A5C"),
        Topic(key="compliance", label="Compliance", color="#8B5CF6"),
    ]
    db.add_all(topics)
    db.commit()
    return {t.key: t for t in topics}


def _mk_users(db):
    db.add_all([
        User(name="Dr. Anita Sharma", role=Role.GEOLOGIST, title="Chief Geologist, CMPDIL",
             subsidiary="CMPDIL", avatar_color="#0B1B2B"),
        User(name="Rajesh Iyer", role=Role.MINISTRY_OFFICIAL, title="Director (Coal), MoC",
             subsidiary="Ministry of Coal", avatar_color="#B7791F"),
        User(name="Meera Krishnan", role=Role.AUDITOR, title="Senior Auditor, CIL",
             subsidiary="CIL", avatar_color="#365F6D"),
    ])
    db.commit()


def _mk_coalfields(db):
    rows = [Coalfield(**c) for c in COALFIELDS]
    db.add_all(rows)
    db.commit()
    return {c.name: c for c in rows}


def _mk_metrics(db):
    import datetime
    starts = datetime.date(2024, 1, 31)
    rows = []
    for i in range(6):
        d = starts.replace(year=starts.year + (i // 4), month=1 + (i % 4) * 3, day=28)
        # trend: prep-time falls, accuracy/automation/resolution rise
        rows.append(MetricSnapshot(
            captured_on=d,
            prep_time_min=max(35, 220 - i * 28),
            extraction_accuracy=88.0 + i * 1.8,
            automation_pct=84.0 + i * 2.2,
            query_resolution_pct=74.0 + i * 3.5,
            docs_processed=10 + i * 3,
            docs_total=18,
        ))
    db.add_all(rows)
    db.commit()


def _mk_audit(db):
    events = [
        ("GEOLOGIST", "uploaded", "Parej East geological report"),
        ("GEOLOGIST", "extracted", "12 structured fields, avg 0.94 conf"),
        ("AUDITOR", "reviewed", "Inconsistency flag on Talcher North reserves"),
        ("MINISTRY_OFFICIAL", "generated_report", "Talcher reserves summary"),
        ("GEOLOGIST", "queried", "Coal grade of Korba Gare Palma IV"),
        ("AUDITOR", "exported_audit_log", "Quarterly QA extract"),
        ("MINISTRY_OFFICIAL", "queried", "Environmental closure rate, Ib Valley"),
    ]
    for role, action, subject in events:
        db.add(AuditEvent(actor_role=role, action=action, subject=subject))
    db.commit()


def build_one_doc(db, coalfields, topics, spec: dict, rng: random.Random) -> tuple[Document, list]:
    """Author one document, run it through the pipeline, return (doc, fields)."""
    coalfield = coalfields[spec["coalfield"]]
    block = {"block": spec["block"], "district": spec["district"]}
    from app.seed.corpus_templates import build_content, render_pdf

    content = build_content(
        rng, coalfield, block, seam=spec["seam"], category=spec["category"],
        report_date=spec["report_date"], outlier_bias=spec.get("outlier", 0.0),
    )

    # 1) render and store the real PDF
    upload_path = Path(settings.uploads_dir) / f"{spec['block'].replace(' ', '-')}.pdf"
    render_pdf(content, str(upload_path))

    doc = Document(
        title=content.title,
        category=DocCategory(spec["category"]),
        coalfield_id=coalfield.id,
        block_name=spec["block"],
        district=content.district,
        source_type=DocSource.PDF,
        status=DocStatus.READY,
        size_bytes=upload_path.stat().st_size,
        file_path=str(upload_path),
        report_date=spec["report_date"],
        ingestion_progress={"step": "READY", "pct": 100, "message": "Complete"},
    )
    db.add(doc)
    db.flush()

    # 2) text layer via pdf_service (real bboxes from the rendered PDF)
    from app.services import pdf_service
    pages, page_count = pdf_service.extract_text_layer(str(upload_path))
    pages_dir = Path(settings.pages_dir) / doc.id
    rendered = pdf_service.render_all_pages(str(upload_path), pages_dir)

    pno_to_db = {}
    page_lines = {}
    for pageresult, r in zip(pages, rendered):
        dp = DocumentPage(
            document_id=doc.id, page_number=r["page_number"], image_path=r["path"],
            width=r["w"], height=r["h"], text=pageresult.text, ocr_conf_mean=pageresult.conf_mean,
        )
        db.add(dp)
        db.flush()
        pno_to_db[r["page_number"]] = dp.id
        page_lines[r["page_number"]] = pageresult.lines

    # 3) emissions
    for pageresult, r in zip(pages, rendered):
        dbpid = pno_to_db[r["page_number"]]
        for ln in pageresult.lines:
            db.add(TextEmission(
                document_id=doc.id, page_id=dbpid,
                text=ln["text"], bbox=ln["bbox"], confidence=ln["conf"],
                char_start=ln["char_start"], char_end=ln["char_end"],
                is_heading=ln.get("is_heading", 0),
            ))
    doc.page_count = page_count
    doc.pages_dir = str(pages_dir)
    db.commit()

    # 4) extraction (same rule path live uploads use)
    from app.services import extraction_service as es
    hits = es.extract_fields_from_pages(list(zip(pages, [r["page_number"] for r in rendered])), {})
    hits = es.resolve_fields_to_emissions(hits, page_lines)

    fields = []
    proof = {}
    confs = []
    for h in hits:
        fe = FieldExtraction(
            document_id=doc.id, page_id=pno_to_db[h.page_number], page_number=h.page_number,
            field_key=h.field_key, field_label=h.field_label, value=h.value,
            unit=h.unit, numeric_value=h.numeric_value, confidence=h.confidence,
            bbox=h.bbox, matched_text=h.matched_text, method=h.method,
        )
        db.add(fe)
        db.flush()
        fields.append(fe)
        proof[h.field_key] = h
        confs.append(h.confidence)
        if h.numeric_value is not None:
            db.add(QuantMetric(
                document_id=doc.id, metric_key=h.field_key, label=h.field_label,
                value=h.numeric_value, unit=h.unit, conf=h.confidence,
            ))
    doc.total_confidence = round(sum(confs) / len(confs), 3) if confs else 0
    db.commit()

    # 5) word stats
    from app.services.insight_service import compute_word_stats
    for w, c in compute_word_stats([p.text or "" for p in pages]):
        db.add(DocumentWord(document_id=doc.id, word=w, count=c))
    db.commit()

    # 6) topics
    tcat = {
        "PROSPECTING": ["exploration", "seam-quality"],
        "GEOLOGICAL_REPORT": ["reserves", "seam-quality"],
        "PRODUCTION": ["production", "compliance"],
        "ENVIRONMENTAL": ["environment", "compliance"],
        "RESERVES": ["reserves", "exploration"],
    }[spec["category"]]
    quarter = spec["quarter"]
    for i, key in enumerate(tcat):
        db.add(DocumentTopic(
            document_id=doc.id, topic_id=topics[key].id,
            weight=round(rng.uniform(0.6, 1.0) - i * 0.1, 3), quarter=quarter,
        ))
    db.commit()

    return doc, fields


def build_reports_and_anomalies(db, coalfields, docs):
    """Auto-generate reports + run anomaly service for every doc."""
    for doc in docs:
        from app.services.ingestion import create_report
        try:
            create_report(doc.id)
        except Exception as exc:
            print(f"  report skip {doc.block_name}: {exc}")

        coalfield = doc.coalfield
        metrics = db.query(QuantMetric).filter(QuantMetric.document_id == doc.id).all()
        fields = db.query(FieldExtraction).filter(FieldExtraction.document_id == doc.id).all()
        proof = {f.field_key: f for f in fields}
        from app.services.anomaly_service import detect
        for a in detect(doc, metrics, coalfield, proof, db):
            db.add(a)
    db.commit()


def build_chat_history(db, docs):
    s = ChatSession(title="Sample query session", language="hi")
    db.add(s)
    db.flush()
    qas = [
        ("पारेज पूर्वी खंड में बिटुमिनस कोयले की गुणवत्ता बताइए", "hi",
         "माननीय महोदय, पारेज पूर्वी खंड सम्बन्धी प्रलेखों के अनुसार मुख्य सीम की गुणवत्ता",
         0.91, ["Parej East", "East Bokaro"]),
        ("Which block shows the highest overburden ratio?", "en",
         "Based on consolidated records, Talcher North reports the highest overburden",
         0.88, ["Talcher North", "Talcher"]),
        ("कोरबा गारे पल्मा ब्लॉक की राख मात्रा क्या है", "hi",
         "गारे पल्मा IV ब्लॉक की राख मात्रा 30.2 % प्रलेखित है",
         0.9, ["Gare Palma IV", "Korba"]),
        ("List the flagged inconsistencies this quarter.", "en",
         "Two high-severity deviations were flagged for Talcher North reserves and Korba GCV.",
         0.84, ["Talcher"]),
    ]
    for q, lang, ans, conf, subs in qas:
        um = ChatMessage(session_id=s.id, role=ChatRole.USER, content=q, language=lang, mode="text")
        db.add(um)
        db.flush()
        sm = ChatMessage(session_id=s.id, role=ChatRole.SYSTEM, content=ans,
                         language=lang, confidence=conf, response_ms=620 + len(q) * 3, mode="text")
        db.add(sm)
        db.flush()
        for rank, sub in enumerate(subs):
            doc = next((d for d in docs if sub.lower() in (d.block_name + d.title).lower()), None)
            if doc is None:
                continue
            fe = (db.query(FieldExtraction).filter(FieldExtraction.document_id == doc.id).first())
            db.add(ChatCitation(
                message_id=sm.id, rank=rank, snippet=ans[:140], document_id=doc.id,
                page_number=1, bbox=fe.bbox if fe else {}, score=0.87 - rank * 0.05,
                document_title=doc.title,
            ))
    db.commit()


def run(verbose: bool = True):
    print("CoalMitra seed: creating schema + corpus ...")
    _wipe()
    db = SessionLocal()
    try:
        topics = _mk_topics(db)
        _mk_users(db)
        coalfields = _mk_coalfields(db)
        _mk_metrics(db)
        _mk_audit(db)

        rng = random.Random(42)
        docs = []

        # Deterministic 18-doc plan across 7 coalfields × 5 categories.
        # Talcher North + Gare Palma IV carry intentional strong outliers
        # (anomaly material).
        plan = []
        for cname in COALFIELDS:
            blocks = BLOCKS[cname["name"]]
            seams = SEAMS[cname["name"]]
            for bi, b in enumerate(blocks):
                cats = ["GEOLOGICAL_REPORT", "PROSPECTING", "RESERVES",
                        "PRODUCTION", "ENVIRONMENTAL", "PROSPECTING", "GEOLOGICAL_REPORT"]
                cat = cats[(bi + len(plan)) % len(cats)]
                quarter = ["2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2", "2024-Q3",
                           "2024-Q4", "2025-Q1", "2025-Q2"][bi % 8]
                outlier = 0.9 if (b["block"] in ("Talcher North", "Gare Palma IV")) else 0.0
                plan.append({
                    "coalfield": cname["name"], "block": b["block"], "district": b["district"],
                    "seam": seams[bi % len(seams)], "category": cat,
                    "report_date": ["2023-09-15", "2023-12-20", "2024-03-12", "2024-06-18",
                                    "2024-09-22", "2025-01-14", "2025-04-09"][bi % 7],
                    "quarter": quarter, "outlier": outlier,
                })

        for spec in plan:
            doc, _ = build_one_doc(db, coalfields, topics, spec, rng)
            docs.append(doc)
            if verbose:
                print(f"  seeded {spec['block']} ({spec['category']}) "
                      f"conf={doc.total_confidence}")

        build_reports_and_anomalies(db, coalfields, docs)
        build_chat_history(db, docs)

        counts = {
            "documents": db.query(Document).count(),
            "fields": db.query(FieldExtraction).count(),
            "emissions": db.query(TextEmission).count(),
            "reports": db.query(Report).count(),
            "anomalies": db.query(Anomaly).count(),
            "topics": db.query(Topic).count(),
            "words": db.query(DocumentWord).count(),
        }
        print("Seed complete:", counts)
    finally:
        db.close()


if __name__ == "__main__":
    run()