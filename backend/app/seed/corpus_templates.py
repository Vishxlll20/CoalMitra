"""Corpus authoring: builds realistic geological-report text and renders it as
a real PDF via PyMuPDF so the extraction pipeline sees genuine coordinates.

The authored text deliberately includes the exact field phrasings that
extraction_service regexes anchor on, e.g. "Gross Calorific Value 4120 kcal/kg".
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import fitz  # PyMuPDF

A4_W, A4_H = 595, 842
MARGIN = 54
FONT = "helv"
SIZE_H1 = 16
SIZE_H2 = 12
SIZE_BODY = 10.5
LINE_GAP = 15


@dataclass
class DocContent:
    title: str
    block: str
    district: str
    coalfield_name: str
    category: str
    report_date: str
    seam: str
    grade: str
    gcv: float
    ash: float
    moisture: float
    ob_ratio: float
    proved_reserve_mt: float
    inferred_reserve_mt: float
    depth_m: float
    area_sqkm: float
    production_mtpa: float
    lines: list[tuple[str, str]]  # (text, kind) kind in {h1,h2,body,hindi}


def _fmt(n: float, dec: int = 1) -> str:
    return f"{n:,.{dec}f}"


def build_content(rng: random.Random, coalfield, block: dict, seam: str,
                  category: str, report_date: str, outlier_bias: float = 0.0) -> DocContent:
    """Compose one document's logical lines + its field truth-values.

    Values drift around coalfield baselines; `outlier_bias` (0..1) pushes a few
    metrics far off-baseline so anomaly detection has real material.
    `coalfield` may be the ORM model or a plain dict (attribute access works on both).
    """
    def val(base: float, spread: float, perturb: float = 1.0) -> float:
        return base * (1 + rng.uniform(-spread, spread) * perturb)

    gcv = val(coalfield.baseline_gcv, 0.035, 1 - outlier_bias) + rng.uniform(0, 40) * outlier_bias * 4
    ash = val(coalfield.baseline_ash, 0.09, 1 + outlier_bias * 0.5)
    moisture = val(9.0, 0.25)
    ob = val(coalfield.baseline_ob_ratio, 0.12, 1 - outlier_bias) + rng.uniform(0, 1) * (outlier_bias * 3)
    proved = val(320.0, 0.35)
    inferred = proved * rng.uniform(0.7, 0.9)
    depth = val(260.0, 0.28)
    area = val(14.0, 0.3)
    production = rng.uniform(2.0, 6.0)

    if outlier_bias > 0.7:
        rng_ = rng
        proved = proved * rng_.uniform(1.18, 1.32)
        gcv = gcv * rng_.uniform(0.98, 1.02) + rng_.uniform(60, 160)

    grade = rng.choice(["G8", "G10", "G12", "G14"])

    lines: list[tuple[str, str]] = []
    category_title = {
        "PROSPECTING": "BOREHOLE PROSPECTING REPORT",
        "GEOLOGICAL_REPORT": "BLOCK GEOLOGICAL REPORT",
        "PRODUCTION": "MONTHLY PRODUCTION RETURN",
        "ENVIRONMENTAL": "ENVIRONMENTAL COMPLIANCE RECORD",
        "RESERVES": "GRADE-WISE RESERVE STATEMENT",
    }.get(category, "GEOLOGICAL REPORT")

    lines.append((f"{category_title}", "h1"))
    lines.append((f"{block['block']} BLOCK, {coalfield.name.upper()} COALFIELD", "h2"))
    lines.append((f"CENTRAL MINE PLANNING & DESIGN INSTITUTE (CMPDIL)", "h2"))
    lines.append(("", "body"))

    lines.append((f"Report Date: {report_date}", "body"))
    lines.append((f"District: {block['district']}", "body"))
    lines.append((f"Block: {block['block']}", "body"))
    lines.append((f"Coalfield: {coalfield.name}", "body"))
    lines.append(("", "body"))

    lines.append(("1. BLOCK AND GEOLOGICAL FRAME", "h2"))
    lines.append((
        f"The {block['block']} block lies within the {coalfield.name} coalfield of "
        f"{coalfield.state}. Surface mapping and exploratory boreholes delineate the "
        f"{seam} seam over an area of {_fmt(area, 1)} sq km. The district administrative "
        f"jurisdiction is {block['district']}.",
        "body"))
    lines.append((
        f"Drilling density achieved 12 boreholes per square kilometre during the "
        f"reconnaissance and preliminary drilling phases. Structural contours indicate a "
        f"gentle eastward dip with no major fault displacement across the projected lease boundary.",
        "body"))
    lines.append(("", "body"))

    lines.append(("2. QUALITY PARAMETERS", "h2"))
    lines.append((f"Gross Calorific Value {_fmt(gcv, 0)} kcal/kg", "body"))
    lines.append((f"Ash Content {_fmt(ash, 1)} %", "body"))
    lines.append((f"Moisture {_fmt(moisture, 1)} %", "body"))
    lines.append((f"Grade {grade}", "body"))
    lines.append((f"कोयला ग्रेड {grade} घोषित", "hindi"))
    lines.append(("", "body"))

    lines.append(("3. SEAM CHARACTERISTICS", "h2"))
    lines.append((f"Seam Name: {seam}", "body"))
    lines.append((f"Seam Depth {_fmt(depth, 0)} m", "body"))
    lines.append((f"Seam thickness ranges 2.1 to 7.8 m across the block", "body"))
    lines.append(("", "body"))

    lines.append(("4. RESERVES AND RATIOS", "h2"))
    lines.append((f"Proved Reserve {_fmt(proved, 1)} Mt", "body"))
    lines.append((f"Inferred Reserve {_fmt(inferred, 1)} Mt", "body"))
    lines.append((f"Overburden Ratio {_fmt(ob, 1)}:1", "body"))
    lines.append((f"Rated Production {_fmt(production, 1)} MTPA", "body"))
    lines.append(("", "body"))

    lines.append(("5. CONCLUSION", "h2"))
    lines.append((
        f"The {block['block']} block is assessed as development-ready with a proved "
        f"reserve of {_fmt(proved, 1)} MT and a stable grade profile. Recommended next "
        f"stage is preparation of the mining scheme and environmental submissions.",
        "body"))

    return DocContent(
        title=f"{block['block']} — {category_title}",
        block=block["block"],
        district=block["district"],
        coalfield_name=coalfield.name,
        category=category,
        report_date=report_date,
        seam=seam,
        grade=grade,
        gcv=gcv, ash=ash, moisture=moisture, ob_ratio=ob,
        proved_reserve_mt=proved, inferred_reserve_mt=inferred,
        depth_m=depth, area_sqkm=area,
        production_mtpa=production,
        lines=lines,
    )


def _devanagari_font():
    """Try to load a Devanagari-capable font; return None if unavailable."""
    for name in ("notosans-devanagari", "liberation-sans", "notosans"):
        try:
            f = fitz.Font(name)
            # verify it can actually produce Devanagari glyphs
            try:
                if f.has_glyph(ord("क")):
                    return f
            except Exception:
                return f
        except Exception:
            continue
    return None


def render_pdf(content: DocContent, out_path: str) -> None:
    """Draw the logical lines onto real A4 pages at tracked y positions.

    Hindi lines render through a Devanagari-capable font when available
    (so the seeded PDF genuinely shows Hindi), otherwise fall back to the
    Devanagari-stripped English rendering so no blank boxes appear.
    """
    doc = fitz.open()
    page = doc.new_page(width=A4_W, height=A4_H)

    hi_font = _devanagari_font()
    # PyMuPDF inserts a latin font by name; for Devanagari we must pass the font
    # xref. Use page.insert_font + insert_text with fontfile-less builtin via
    # fitz.Font and page.get_textbox tricks is heavy — simplest reliable route:
    # use insert_text with fontname for latin, and insert_htmlbox won't work on
    # older builds. We insert Hindi with fontname="helv" replaced by a text
    # layer authored directly (Emissions), while the visible glyph is drawn via
    # a builtin CJK-agnostic path. To keep the PDF readable, if a Devanagari
    # font is present we register it with the page and use it by xref.
    hi_xref = None
    if hi_font is not None:
        try:
            hi_xref = page.insert_font(fontname="hi", fontbuffer=hi_font.buffer)
        except Exception:
            hi_xref = None

    y = MARGIN
    for text, kind in content.lines:
        if y > A4_H - MARGIN - 20:
            page = doc.new_page(width=A4_W, height=A4_H)
            y = MARGIN
            if hi_font is not None:
                try:
                    hi_xref = page.insert_font(fontname="hi", fontbuffer=hi_font.buffer)
                except Exception:
                    hi_xref = None
        if text == "":
            y += LINE_GAP * 0.5
            continue
        size = SIZE_H1 if kind == "h1" else SIZE_H2 if kind == "h2" else SIZE_BODY
        use_hi = kind == "hindi" and hi_xref is not None
        baseline = y + size * 0.8
        if use_hi:
            # fontname="hi" registered via buffer; PyMuPDF accepts the alias
            page.insert_text((MARGIN, baseline), text, fontsize=size,
                             fontname="hi", color=(0.05, 0.09, 0.13))
        else:
            rendered_text = text if kind != "hindi" else _latin_fallback(text)
            page.insert_text((MARGIN, baseline), rendered_text, fontsize=size,
                             fontname=FONT, color=(0.05, 0.09, 0.13))
        y += size * 0.8 + (6 if kind in ("h1", "h2") else 2)
        if kind == "h1":
            y += 6

    doc.save(out_path)
    doc.close()


def _latin_fallback(text: str) -> str:
    """Drop non-latin chars so the PDF never shows blank glyph boxes."""
    import re
    return re.sub(r"[^\x00-\x7F]+", " ", text).strip() or "Grade declared"