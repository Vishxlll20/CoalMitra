"""Ingestion pipeline orchestrator.

Runs OCR/text-layer → extraction → indexing → reporting for one document.
Shared by live uploads (background task) and the seed builder (synchronous).
Writes `documents.ingestion_progress` as it goes so the frontend stepper can
poll and animate each stage.
"""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from datetime import date
from types import SimpleNamespace

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import (
    Document,
    DocumentTopic,
    DocStatus,
    DocumentPage,
    FieldExtraction,
    QuantMetric,
    TextEmission,
)
from app.models.report import Report
from app.services.insight_service import compute_word_stats

_STEP_TO_STATUS = {
    "UPLOADING": DocStatus.UPLOADING,
    "OCR": DocStatus.OCR,
    "EXTRACTING": DocStatus.EXTRACTING,
    "INDEXING": DocStatus.INDEXING,
    "REPORTING": DocStatus.REPORTING,
    "READY": DocStatus.READY,
    "FAILED": DocStatus.FAILED,
}


def _set_progress(db, doc_id: str, step: str, pct: int, message: str):
    doc = db.query(Document).get(doc_id)
    if doc is None:
        return
    doc.status = _STEP_TO_STATUS.get(step.upper(), DocStatus.READY)
    doc.ingestion_progress = {"step": step, "pct": pct, "message": message}
    db.add(doc)
    db.commit()


def ingest_document(doc_id: str):
    """Run the full pipeline for an uploaded document (background task)."""
    db = SessionLocal()
    try:
        doc = db.query(Document).get(doc_id)
        if doc is None:
            return

        _set_progress(db, doc_id, "UPLOADING", 10, "File received")
        pdf_path = doc.file_path
        if not pdf_path or not Path(pdf_path).exists():
            _set_progress(db, doc_id, "FAILED", 0, "Missing file")
            return

        from app.services import pdf_service

        _set_progress(db, doc_id, "OCR", 40, "Extracting page text")
        pages, page_count = pdf_service.extract_text_layer(pdf_path)
        _set_progress(db, doc_id, "OCR", 45, f"Text layer done ({page_count} pages)")
        _populate_document_metadata(db, doc, pages)

        # Render page PNGs
        pages_dir = Path(settings.pages_dir) / doc_id
        rendered = pdf_service.render_all_pages(pdf_path, pages_dir)
        pno_to_db_page = {}
        page_lines = {}
        for pageresult, r in zip(pages, rendered):
            db_page = DocumentPage(
                document_id=doc_id,
                page_number=r["page_number"],
                image_path=r["path"],
                width=r["w"],
                height=r["h"],
                text=pageresult.text,
                ocr_conf_mean=pageresult.conf_mean,
            )
            db.add(db_page)
            db.flush()
            pno_to_db_page[r["page_number"]] = db_page.id
            page_lines[r["page_number"]] = pageresult.lines
        doc.page_count = page_count
        doc.pages_dir = str(pages_dir)
        db.add(doc)

        # Emit text layer
        _set_progress(db, doc_id, "EXTRACTING", 60, "Storing text layer")
        for pageresult, r in zip(pages, rendered):
            db_page_id = pno_to_db_page[r["page_number"]]
            for ln in pageresult.lines:
                db.add(TextEmission(
                    document_id=doc_id,
                    page_id=db_page_id,
                    line_no=ln.get("line_no", 0),
                    text=ln["text"],
                    bbox=ln["bbox"],
                    confidence=ln["conf"],
                    char_start=ln["char_start"],
                    char_end=ln["char_end"],
                    is_heading=ln.get("is_heading", 0),
                ))
        db.commit()

        # Field extraction via the SAME rule path live uploads use
        _set_progress(db, doc_id, "EXTRACTING", 70, "Matching fields")
        from app.services import extraction_service

        hits = extraction_service.extract_fields_from_pages(list(zip(pages, [r["page_number"] for r in rendered])), {})
        hits = extraction_service.resolve_fields_to_emissions(hits, page_lines)
        proof_fields = {}
        confs = []
        for h in hits:
            db.add(FieldExtraction(
                document_id=doc_id,
                page_id=pno_to_db_page[h.page_number],
                page_number=h.page_number,
                field_key=h.field_key,
                field_label=h.field_label,
                value=h.value,
                unit=h.unit,
                numeric_value=h.numeric_value,
                confidence=h.confidence,
                bbox=h.bbox,
                matched_text=h.matched_text,
                method=h.method,
            ))
            proof_fields[h.field_key] = h
            confs.append(h.confidence)
        db.flush()

        # QuantMetrics mirror numeric fields for anomaly/report math
        for h in hits:
            if h.numeric_value is not None:
                db.add(QuantMetric(
                    document_id=doc_id,
                    metric_key=h.field_key,
                    label=h.field_label,
                    value=h.numeric_value,
                    unit=h.unit,
                    conf=h.confidence,
                ))
        doc.total_confidence = round(sum(confs) / len(confs), 3) if confs else 0
        db.add(doc)
        db.commit()

        _set_progress(db, doc_id, "INDEXING", 85, "Indexing chunks")
        index_document_pages(db, doc_id, pno_to_db_page)

        # Word stats
        _set_progress(db, doc_id, "REPORTING", 95, "Words + report")
        page_rows = db.query(DocumentPage).filter(DocumentPage.document_id == doc_id).all()
        word_stats = compute_word_stats([p.text or "" for p in page_rows])
        from app.models import DocumentWord
        for w, c in word_stats[:150]:
            db.add(DocumentWord(document_id=doc_id, word=w, count=c))
        db.commit()

        _assign_topics_and_detect_anomalies(db, doc_id)

        # Auto report
        create_report(doc_id)

        _set_progress(db, doc_id, "READY", 100, "Complete — report generated")
        doc.status = DocStatus.READY
        db.add(doc)
        db.commit()
    except Exception as exc:
        try:
            _set_progress(db, doc_id, "FAILED", 0, str(exc)[:160])
        except Exception:
            pass
    finally:
        db.close()


def _assign_topics_and_detect_anomalies(db, doc_id: str) -> None:
    """Attach category topics and compare extracted metrics with block history."""
    from app.models import Coalfield, DocumentTopic, FieldExtraction, QuantMetric, Topic
    from app.models.report import Anomaly
    from app.services.anomaly_service import detect

    doc = db.query(Document).get(doc_id)
    if doc is None:
        return

    category_topics = {
        "PROSPECTING": ("exploration", "seam-quality"),
        "GEOLOGICAL_REPORT": ("reserves", "seam-quality"),
        "PRODUCTION": ("production", "compliance"),
        "ENVIRONMENTAL": ("environment", "compliance"),
        "RESERVES": ("reserves", "exploration"),
    }.get(doc.category.value if doc.category else "", ("exploration", "compliance"))
    page_text = " ".join(
        page.text or ""
        for page in db.query(DocumentPage)
        .filter(DocumentPage.document_id == doc_id)
        .order_by(DocumentPage.page_number)
        .all()
    )
    from app.services.insight_service import infer_topic_weights
    inferred_topics = infer_topic_weights(page_text)
    topic_weights = inferred_topics or [(key, round(0.85 - i * 0.1, 3)) for i, key in enumerate(category_topics)]
    quarter = _report_quarter(doc.report_date)
    topic_keys = [key for key, _ in topic_weights]
    topic_rows = {topic.key: topic for topic in db.query(Topic).filter(Topic.key.in_(topic_keys)).all()}
    existing = {row.topic_id for row in db.query(DocumentTopic).filter(DocumentTopic.document_id == doc_id).all()}
    for key, weight in topic_weights:
        topic = topic_rows.get(key)
        if topic is not None and topic.id not in existing:
            db.add(DocumentTopic(
                document_id=doc_id,
                topic_id=topic.id,
                weight=weight,
                quarter=quarter,
            ))
    db.commit()

    if not doc.coalfield:
        return
    metrics = db.query(QuantMetric).filter(QuantMetric.document_id == doc_id).all()
    fields = db.query(FieldExtraction).filter(FieldExtraction.document_id == doc_id).all()
    proof = {field.field_key: field for field in fields}
    previous = None
    if doc.block_name and doc.block_name.strip():
        previous = (
            db.query(Document)
            .filter(
                Document.id != doc_id,
                Document.coalfield_id == doc.coalfield_id,
                Document.block_name == doc.block_name,
            )
            .order_by(Document.uploaded_at.desc())
            .first()
        )
    comparison = _historical_baseline(db, doc, previous) if previous else doc.coalfield
    anomalies = detect(doc, metrics, comparison, proof, db)
    for anomaly in anomalies:
        baseline_source = previous
        if baseline_source is None:
            baseline_source = (
                db.query(Document)
                .join(QuantMetric, QuantMetric.document_id == Document.id)
                .filter(
                    Document.id != doc_id,
                    Document.coalfield_id == doc.coalfield_id,
                    QuantMetric.metric_key == anomaly.metric_key,
                )
                .order_by(Document.uploaded_at.desc())
                .first()
            )
        if baseline_source:
            anomaly.baseline_document_id = baseline_source.id
        db.add(anomaly)
    db.commit()


def _populate_document_metadata(db, doc: Document, pages) -> None:
    """Fill block, district, date, and known coalfield from the source text."""
    from app.models import Coalfield

    text = "\n".join(page.text or "" for page in pages)
    if not text.strip():
        return
    for attribute, label in (("block_name", "Block"), ("district", "District")):
        if getattr(doc, attribute):
            continue
        match = re.search(rf"(?im)^\s*{label}\s*:\s*([^|\r\n]{{1,120}})", text)
        if match:
            setattr(doc, attribute, match.group(1).strip())

    if not doc.report_date:
        match = re.search(r"(?im)^\s*Report\s+Date\s*:\s*(\d{4}-\d{2}-\d{2})", text)
        if match:
            doc.report_date = match.group(1)

    if not doc.coalfield_id:
        declared = re.search(r"(?im)^\s*Coalfield\s*:\s*([^\r\n]{1,120})", text)
        if declared:
            requested = re.sub(r"\s+", " ", declared.group(1)).strip().casefold()
            for coalfield in db.query(Coalfield).all():
                if re.sub(r"\s+", " ", coalfield.name).strip().casefold() == requested:
                    doc.coalfield_id = coalfield.id
                    break
    db.add(doc)
    db.commit()


def _historical_baseline(db, doc, previous):
    from app.models import QuantMetric

    values = {
        metric.metric_key: metric.value
        for metric in db.query(QuantMetric).filter(QuantMetric.document_id == previous.id).all()
    }
    field_to_baseline = {
        "gcv": "baseline_gcv",
        "ash_content": "baseline_ash",
        "ob_ratio": "baseline_ob_ratio",
        "proved_reserve_mt": "reserve_mt",
    }
    baseline = {
        field: values.get(key, getattr(doc.coalfield, field, 0))
        for key, field in field_to_baseline.items()
    }
    baseline["name"] = f"prior filing for {previous.block_name}"
    return SimpleNamespace(**baseline)


def _report_quarter(report_date: str | None) -> str:
    try:
        parsed = date.fromisoformat((report_date or "")[:10])
        return f"{parsed.year}-Q{((parsed.month - 1) // 3) + 1}"
    except ValueError:
        return ""


def migrate_legacy_field_units(db=None) -> int:
    """Repair units and stored report refs written by older unit inference."""
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    from app.models import QuantMetric

    expected_units = {
        "gcv": "kcal/kg",
        "ash_content": "%",
        "moisture": "%",
        "proved_reserve_mt": "MT",
        "inferred_reserve_mt": "MT",
        "grade": "",
        "ob_ratio": ":1",
        "depth_m": "m",
        "area_sqkm": "sq km",
        "production_mtpa": "MTPA",
        "report_date": "",
        "district": "",
        "block": "",
    }
    changed = 0
    try:
        fields_by_document: dict[str, list[FieldExtraction]] = {}
        for field in db.query(FieldExtraction).all():
            expected = expected_units.get(field.field_key)
            if expected is not None and field.unit != expected:
                field.unit = expected
                changed += 1
            fields_by_document.setdefault(field.document_id, []).append(field)

        for metric in db.query(QuantMetric).all():
            expected = expected_units.get(metric.metric_key)
            if expected is not None and metric.unit != expected:
                metric.unit = expected
                changed += 1

        for report in db.query(Report).all():
            fields = fields_by_document.get(report.document_id, [])
            updated = False
            sections = deepcopy(report.sections or [])
            for section in sections:
                for ref in section.get("refs", []):
                    for field in fields:
                        same_page = int(ref.get("page", 0) or 0) == int(field.page_number or 0)
                        same_value = ref.get("value") == (
                            field.numeric_value if field.numeric_value is not None else field.value
                        )
                        if not same_page or not same_value:
                            continue
                        display = f"{field.value}{(' ' + field.unit) if field.unit else ''}"
                        if ref.get("display") != display:
                            ref["display"] = display
                            updated = True
                        break
            if updated:
                report.sections = sections
                report.pdf_path = ""
                changed += 1

        from app.models.report import Anomaly
        for anomaly in db.query(Anomaly).filter(Anomaly.baseline_document_id == "").all():
            baseline = (
                db.query(Document)
                .join(QuantMetric, QuantMetric.document_id == Document.id)
                .filter(
                    Document.id != anomaly.document_id,
                    Document.coalfield_id == anomaly.coalfield_id,
                    QuantMetric.metric_key == anomaly.metric_key,
                )
                .order_by(Document.uploaded_at.desc())
                .first()
            )
            if baseline:
                anomaly.baseline_document_id = baseline.id
                changed += 1
        if changed:
            db.commit()
        return changed
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def index_document_pages(db, doc_id: str, pno_to_db_page: dict[int, str]):
    """Chunk + upsert a document's pages into the vector index.

    Also populates back-references needed by demo keyword search (the demo path
    queries text_emissions directly, so this helper mainly exists for the real
    chroma path and is a no-op when chroma isn't available).
    """
    pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc_id).order_by(DocumentPage.page_number).all()
    if not pages:
        return
    chunk_size = 700
    from app.models import TextEmission as TE
    for p in pages:
        emissions = db.query(TE).filter(TE.page_id == p.id).order_by(TE.line_no).all()
        lines = [e.text for e in emissions if e.text.strip()]
        chunks = _chunk_lines(lines, chunk_size)
        for i, chunk in enumerate(chunks):
            # start char offset approximate — scan emissions for the first line
            first_line = chunk.split("\n")[0]
            start = next((e.char_start for e in emissions if e.text == first_line), 0)
            from app.services.index_service import get_collection
            col = get_collection()
            col.upsert(
                ids=[f"{doc_id}:p{p.page_number}:c{i}"],
                documents=[chunk],
                metadatas=[{
                    "document_id": doc_id,
                    "title": db.query(Document).get(doc_id).title,
                    "page_number": p.page_number,
                    "char_start": start,
                    "char_end": start + len(chunk),
                    "bbox": _first_box(emissions),
                }],
            )


def _chunk_lines(lines: list[str], size: int) -> list[str]:
    chunks, cur = [], ""
    for ln in lines:
        if len(cur) + len(ln) > size and cur:
            chunks.append(cur)
            cur = ln
        else:
            cur = (cur + "\n" + ln).strip()
    if cur:
        chunks.append(cur)
    return chunks


def _first_box(emissions):
    for e in emissions:
        if e.bbox:
            return e.bbox
    return {}


def create_report(doc_id: str) -> Report | None:
    """Generate the auto report for a document (current demo path)."""
    db = SessionLocal()
    try:
        doc = db.query(Document).get(doc_id)
        if doc is None:
            return None
        fields = db.query(FieldExtraction).filter(FieldExtraction.document_id == doc_id).all()
        metrics = db.query(QuantMetric).filter(QuantMetric.document_id == doc_id).all()

        from app.services.report_service import build_report_sections

        sections = build_report_sections(doc, fields, metrics)
        report_subject = doc.block_name.strip() if doc.block_name else Path(doc.title).stem
        title = f"{report_subject or 'Document'} — Geological Summary"
        report = Report(
            document_id=doc_id,
            title=title,
            template_type="standard",
            sections=sections,
            narrative={"summary": sections[0]["body"][0] if sections else ""},
            status="GENERATED",
            source_count=len(fields),
        )
        db.add(report)
        db.commit()
        # Re-load attributes while the session is still open so the returned
        # object stays readable (sections/narrative) after close.
        db.refresh(report)
        return report
    finally:
        db.close()