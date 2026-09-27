"""Structured field extraction from page text with bbox + confidence.

Matching runs against the FULL page text (so values wrapped across visual
lines are still found), then each hit resolves to the text-emission line that
contains its char span to lock the bbox. Confidence reflects how precisely the
anchor matched:
   1.0   exact phrase + unit present
   0.95  phrase present, unit inferred
   0.90  loose phrase match
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.text import FIELD_PATTERNS, FIELD_LABELS, num


@dataclass
class FieldHit:
    field_key: str
    field_label: str
    value: str
    unit: str
    confidence: float
    page_number: int
    bbox: dict
    matched_text: str
    char_start: int
    char_end: int
    method: str = "rule"
    numeric_value: float | None = None


_NUM_HINTS = {
    "gcv": ["gross calorific value", "gcv", "गरमी मूल्य", "calorific"],
    "ash_content": ["ash content", "ash", "राख"],
    "moisture": ["moisture", "नमी"],
    "ob_ratio": ["overburden", "ob ratio", "obr", "अंत: कार्य"],
    "proved_reserve_mt": ["proved reserve", "सिद्ध भंडार", "proved"],
    "production_mtpa": ["production", "उत्पादन", "mtpa"],
    "area_sqkm": ["area", "क्षेत्रफल"],
}


def extract_fields_from_pages(pages, page_map: dict) -> list[FieldHit]:
    """Extract fields across a document's pages.

    Args:
        pages: list of (PageTextResult, page_number).
    Returns FieldHit list (page_number 1-based, bbox normalized).
    """
    hits: list[FieldHit] = []

    for pageresult, pno in pages:
        full = pageresult.text or ""
        if not full.strip():
            continue
        for key, pattern in FIELD_PATTERNS.items():
            m = re.search(pattern, full, re.IGNORECASE)
            if not m:
                continue
            value = m.group(1).strip()
            unit = _unit_for(full[m.start():m.end()], key) or _unit_near(full, m.start(), key)
            confidence = _confidence(full[m.start():m.start() + 60], key, unit)
            # locate containing emission line for an exact bbox
            line = _line_containing(pageresult.lines, m.start(), m.end())
            if line is None:
                continue
            hits.append(FieldHit(
                field_key=key,
                field_label=FIELD_LABELS.get(key, key.replace("_", " ").title()),
                value=value,
                unit=unit,
                confidence=confidence,
                page_number=pno,
                bbox=line["bbox"],
                matched_text=full[max(0, m.start() - 40):m.end() + 30].strip(),
                char_start=line["char_start"],
                char_end=line["char_end"],
                numeric_value=num(value),
            ))

    return hits


def _line_containing(lines: list[dict], start: int, end: int):
    for ln in lines:
        if ln["char_start"] <= start <= ln["char_end"]:
            return ln
    # fall back to nearest line by start-distance
    if lines:
        return min(lines, key=lambda ln: abs(ln["char_start"] - start))
    return None


def _unit_for(match_text: str, key: str) -> str:
    lowered = match_text.lower()
    if key == "gcv" and ("kcal" in lowered or "kj" in lowered):
        return "kcal/kg"
    if key in {"proved_reserve_mt", "inferred_reserve_mt"} and ("million" in lowered or re.search(r"\bmt\b", lowered)):
        return "MT"
    if key in {"ash_content", "moisture"} and "%" in lowered:
        return "%"
    if key == "ob_ratio":
        return ":1"
    return {"depth_m": "m", "area_sqkm": "sq km", "production_mtpa": "MTPA"}.get(key, "")


def _unit_near(full: str, pos: int, key: str) -> str:
    line_start = full.rfind("\n", 0, pos) + 1
    line_end = full.find("\n", pos)
    if line_end < 0:
        line_end = len(full)
    window = full[line_start:line_end]
    u = _unit_for(window, key)
    return u


def _confidence(text: str, key: str, unit: str) -> float:
    conf = 0.9
    if unit:
        conf += 0.05
    flat = re.sub(r"\s+", " ", text.lower())
    if any(k in flat for k in _NUM_HINTS.get(key, [])):
        conf += 0.02
    return round(min(0.99, conf), 3)


def resolve_fields_to_emissions(hits: list[FieldHit], page_lines: dict[int, list[dict]]) -> list[FieldHit]:
    """Snap each hit's bbox to the most specific containing emission."""
    for h in hits:
        candidates = page_lines.get(h.page_number, [])
        best = next((ln for ln in candidates
                     if ln["char_start"] <= h.char_start <= ln["char_end"]), None)
        if best:
            h.bbox = best["bbox"]
            h.char_start = best["char_start"]
            h.char_end = best["char_end"]
    return hits