"""Ingestion pipeline orchestrator.

Runs OCR/text-layer → extraction → indexing → reporting for one document.
Shared by live uploads (background task) and the seed builder (synchronous).
Writes `documents.ingestion_progress` as it goes so the frontend stepper can
poll and animate each stage.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import (
    Document,
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
        if doc is None or doc.block_name is None:
            return None
        fields = db.query(FieldExtraction).filter(FieldExtraction.document_id == doc_id).all()
        metrics = db.query(QuantMetric).filter(QuantMetric.document_id == doc_id).all()

        from app.services.report_service import build_report_sections

        sections = build_report_sections(doc, fields, metrics)
        title = f"{doc.block_name or doc.title} — Geological Summary"
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