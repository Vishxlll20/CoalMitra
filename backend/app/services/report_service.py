"""Auto report generation.

Takes a document's FieldExtractions + QuantMetrics and compiles an ordered
set of narrative/table sections. Every number is emitted as a ref carrying
{value, display, page, bbox, confidence, document_id} — the traceability
contract that makes report numbers clickable back to the source page.
"""
from __future__ import annotations

from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

def _fmt(n: float | None) -> str:
    if n is None:
        return "—"
    return f"{n:,.2f}".rstrip("0").rstrip(".")


def _metric_view(obj):
    """Present either a FieldExtraction or QuantMetric with a common interface.

    FieldExtraction exposes numeric_value/page_number/bbox/confidence; QuantMetric
    exposes value/unit/conf. Normalize both so ref building is uniform.
    """
    from types import SimpleNamespace

    if obj is None:
        return None
    if hasattr(obj, "numeric_value"):
        return obj
    return SimpleNamespace(
        numeric_value=obj.value,
        value=obj.value,
        unit=getattr(obj, "unit", ""),
        page_number=1,
        bbox=getattr(obj, "bbox", {}),
        confidence=getattr(obj, "conf", getattr(obj, "confidence", 0)),
    )


def build_report_sections(doc, fields: list, metrics: list) -> list[dict]:
    """Given a doc+fields+metrics, return ordered section dicts.

    Section shape:
      {"kind": "narrative"|"table", "title": str, "body": [paragraphs],
       "table": {headers, rows}, "refs": [ {value, display, page, bbox,
       confidence, document_id}* ]}
    """
    f = {x.field_key: x for x in fields}
    m = {x.metric_key: x for x in metrics}
    doc_id = doc.id
    sections = []

    # --- 1. Executive summary (narrative with clickable numbers) ---
    refs = []
    lines = []
    block = doc.block_name or "the block"

    reserve = _metric_view(f.get("proved_reserve_mt") or m.get("proved_reserve_mt"))
    reserve_txt = _fmt(reserve.numeric_value) if reserve and reserve.numeric_value else "—"
    if reserve and (reserve.numeric_value is not None):
        refs.append({
            "value": reserve.numeric_value, "display": f"{reserve_txt} MT",
            "page": reserve.page_number, "bbox": reserve.bbox,
            "confidence": reserve.confidence, "document_id": doc_id,
        })

    gcv = _metric_view(f.get("gcv") or m.get("gcv"))
    gcv_txt = _fmt(gcv.numeric_value) if gcv and gcv.numeric_value else "—"
    if gcv and (gcv.numeric_value is not None):
        refs.append({
            "value": gcv.numeric_value, "display": f"{gcv_txt} kcal/kg",
            "page": gcv.page_number, "bbox": gcv.bbox,
            "confidence": gcv.confidence, "document_id": doc_id,
        })

    lines.append(
        f"This report consolidates geological findings for {block}, drawn from "
        f"prospecting and survey records. Proved reserves are assessed at {reserve_txt} MT, "
        f"with a representative gross calorific value of {gcv_txt} kcal/kg. "
        "The source documents, page coordinates, and extraction confidence for each "
        "figure are embedded inline and available on click."
    )
    sections.append({
        "kind": "narrative",
        "title": "Executive Summary",
        "body": lines,
        "refs": refs,
    })

    # --- 2. Seam table ---
    rows = []
    for key, lbl in (("seam_name", "Seam"), ("grade", "Grade"), ("depth_m", "Depth (m)"),
                     ("ash_content", "Ash (%)"), ("moisture", "Moisture (%)"),
                     ("area_sqkm", "Area (sq km)")):
        hit = f.get(key)
        if not hit:
            continue
        rows.append([lbl, hit.value or "—", hit.confidence])
        refs.append({
            "value": hit.numeric_value if hit.numeric_value is not None else hit.value,
            "display": f"{hit.value}{(' ' + hit.unit) if hit.unit else ''}",
            "page": hit.page_number, "bbox": hit.bbox,
            "confidence": hit.confidence, "document_id": doc_id,
        })
    if rows:
        sections.append({
            "kind": "table",
            "title": "Geological Parameters",
            "table": {"headers": ["Parameter", "Value", "Extraction Confidence"], "rows": rows},
            "refs": refs,
        })

    # --- 3. Reserve context ---
    ob = _metric_view(f.get("ob_ratio") or m.get("ob_ratio"))
    prod = _metric_view(f.get("production_mtpa") or m.get("production_mtpa"))
    remainder = []
    if ob and ob.numeric_value is not None:
        remainder.append(f"The overburden ratio for {block} is {_fmt(ob.numeric_value)}:1")
        refs.append({
            "value": ob.numeric_value, "display": f"{_fmt(ob.numeric_value)}:1",
            "page": ob.page_number, "bbox": ob.bbox, "confidence": ob.confidence,
            "document_id": doc_id,
        })
    if prod and prod.numeric_value is not None:
        remainder.append(f"rated production is {_fmt(prod.numeric_value)} MTPA")
        refs.append({
            "value": prod.numeric_value, "display": f"{_fmt(prod.numeric_value)} MTPA",
            "page": prod.page_number, "bbox": prod.bbox, "confidence": prod.confidence,
            "document_id": doc_id,
        })
    if remainder:
        sections.append({
            "kind": "narrative",
            "title": "Operational Context",
            "body": [", and ".join(remainder) + "."],
            "refs": refs,
        })

    return sections


def render_report_pdf(title: str, sections: list[dict], out_path: str) -> str:
    """Render report sections to a PDF via reportlab. Returns out_path."""
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("CoalH1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                        fontSize=18, leading=22, spaceAfter=12, textColor=colors.HexColor("#0B1B2B"))
    kicker = ParagraphStyle("Kicker", parent=styles["Normal"], fontSize=9,
                            textColor=colors.HexColor("#B7791F"), spaceAfter=4)
    body = ParagraphStyle("CoalBody", parent=styles["BodyText"], fontSize=10.5, leading=15)
    cell = ParagraphStyle("Cell", parent=styles["BodyText"], fontSize=9.5, leading=12)

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    story.append(Paragraph(f"CoalMitra — {title}", h1))
    story.append(Spacer(1, 10))

    for sec in sections:
        story.append(Paragraph(sec.get("title", "").upper(), kicker))
        if sec["kind"] == "narrative":
            for para in sec.get("body", []):
                story.append(Paragraph(para, body))
        else:
            t = sec.get("table", {})
            header = [Paragraph(h, cell) for h in t.get("headers", [])]
            rows = [[Paragraph(str(c) if isinstance(c, str) else str(c), cell) for c in r]
                    for r in t.get("rows", [])]
            data = [header] + rows
            tbl = Table(data, colWidths=[130, 200, None])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2E7CE")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0B1B2B")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8D3C8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 10))

    story.append(Spacer(1, 18))
    story.append(Paragraph(f"Generated by CoalMitra on {date.today().isoformat()}. "
                           "Figures embed source-page coordinates for traceability.", body))
    doc.build(story)
    return out_path