"""PDF text-layer + page rendering via PyMuPDF.

The traceability backbone: every page's words/lines carry real pixel bboxes
which are normalized and stored in text_emissions. Page PNGs are rendered at
2x for crisp overlay highlighting in the frontend.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.utils.bbox import normalize


class PageTextResult:
    """Output of text layer extraction for one page."""

    def __init__(self, text: str, lines, width: int, height: int, conf_mean: float):
        self.text = text
        self.lines = lines          # list[dict]: {text, bbox(norm), conf, is_heading, char_start, char_end}
        self.width = width
        self.height = height
        self.conf_mean = conf_mean


def _is_heading(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if len(t) < 3 or len(t) > 80:
        return False
    # Headings often all-caps or capitalised short lines
    if t.isupper():
        return True
    return re.match(r"^[A-Z][\w\s\-&/]{2,60}$", t) is not None and len(t.split()) <= 8


def extract_text_layer(pdf_path: str) -> tuple[list[PageTextResult], int]:
    """Extract per-page text layer (word-level bboxes) from a PDF.

    Returns (pages, page_count). Client code picks up blocks via page.get_text.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    pages: list[PageTextResult] = []
    char_offset = 0

    for pno in range(len(doc)):
        page = doc[pno]
        pw, ph = page.rect.width, page.rect.height
        page_text = page.get_text("text")
        text_page = None
        if not page_text.strip():
            try:
                text_page = page.get_textpage_ocr(language="eng+hin", dpi=200)
                page_text = page.get_text("text", textpage=text_page)
            except Exception as exc:
                doc.close()
                raise RuntimeError(
                    "This page is an image scan and needs Tesseract OCR (English and Hindi) installed."
                ) from exc
        lines = []
        # word-level blocks with coordinates
        text_dict = page.get_text("dict", textpage=text_page) if text_page else page.get_text("dict")
        for block in text_dict["blocks"]:
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                if not line_text.strip():
                    continue
                x0 = min(s["bbox"][0] for s in line["spans"]) if line["spans"] else 0
                y0 = line["bbox"][1]
                x1 = max(s["bbox"][2] for s in line["spans"]) if line["spans"] else 0
                y1 = line["bbox"][3]
                norm = normalize(x0, y0, x1, y1, pw, ph)
                # em spaces collapse in text extraction; match via index
                h = _is_heading(line_text)
                lines.append({
                    "text": line_text,
                    "bbox": norm,
                    "conf": 0.999,          # digital PDF text layer is near-certain
                    "is_heading": 1 if h else 0,
                })
        # Assign char spans within whole-page text
        full = page_text
        cursor = 0
        for ln in lines:
            t = ln["text"]
            idx = full.find(t, cursor)
            if idx == -1:
                idx = max(full.find(t[:15]), 0) or 0
            ln["char_start"] = char_offset + idx
            ln["char_end"] = ln["char_start"] + len(t)
            cursor = idx + len(t)
        char_offset += len(full) + 1

        conf_mean = sum(l["conf"] for l in lines) / len(lines) if lines else 0
        pages.append(PageTextResult(full, lines, int(pw), int(ph), conf_mean))

    count = len(doc)
    doc.close()
    return pages, count


def render_page_png(pdf_path: str, page_number: int, out_path: str, zoom: float = 2.0) -> tuple[int, int]:
    """Render one page to PNG at `zoom` (2x crispness). Returns (w,h)."""
    import fitz

    doc = fitz.open(pdf_path)
    page = doc[page_number]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    pix.save(out_path)
    w, h = pix.width, pix.height
    doc.close()
    return w, h


def render_all_pages(pdf_path: str, out_dir: Path, zoom: float = 2.0) -> list[dict]:
    """Render every page to PNG in out_dir. Returns list of {page_number, path, w, h}."""
    import fitz

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    rendered = []
    mat = fitz.Matrix(zoom, zoom)
    for pno in range(len(doc)):
        page = doc[pno]
        pix = page.get_pixmap(matrix=mat)
        path = out_dir / f"{pno + 1}.png"
        pix.save(str(path))
        rendered.append({"page_number": pno + 1, "path": str(path), "w": pix.width, "h": pix.height})
    doc.close()
    return rendered