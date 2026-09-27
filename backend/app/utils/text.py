"""Text utilities: cleanup, EN+HI tokenizer, stopwords, field lexicons."""

import re

EN_STOPWORDS = {
    "the", "and", "of", "in", "on", "for", "with", "as", "at", "by", "to", "is", "are",
    "was", "were", "been", "be", "an", "a", "or", "this", "that", "these", "those", "it",
    "from", "per", "which", "its", "each", "has", "have", "will", "shall", "may", "mt",
    "fig", "sr", "no", "the", "table", "appendix", "annexure", "ref", "see", "page", "co",
    "km", "m", "sq", "east", "west", "north", "south", "total", "figure", "rsl", "bgl",
}

HI_STOPWORDS = {
    "को", "के", "की", "में", "से", "पर", "है", "हैं", "और", "या", "का", "कि", "में", "इस",
    "यह", "वह", "गया", "गई", "ना", "भी", "तक", "लिए", "बाद", "था", "थे", "एक", "ही", "पर्यंत",
    "आदि", "सभी", "अधिक", "कम", "अनुसार", "सेतु", "एवं", "चाहिए", "कर", "किया", "जाता",
    "जाती", "हो", "होता", "होगी", "ने", "द्वारा", "वाले", "प्रति", "लगभग",
}

_MERGE_WS = re.compile(r"\s+")
_GARBAGE = re.compile(r"[^\wऀ-ॿ\s]")

STOPWORDS = EN_STOPWORDS | HI_STOPWORDS


def clean(text: str) -> str:
    if not text:
        return ""
    text = _GARBAGE.sub(" ", text)
    text = _MERGE_WS.sub(" ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """EN + Devanagari tokenization with stopword + lowercase filter."""
    tokens = []
    for w in re.findall(r"[\wऀ-ॿ]+", text.lower()):
        if w not in STOPWORDS and len(w) > 1:
            tokens.append(w)
    return tokens


# Field lexicon: phrase patterns matched against page text (in order of precedence)
FIELD_LABELS = {
    "gcv": "Gross Calorific Value",
    "ash_content": "Ash Content",
    "moisture": "Moisture",
    "ob_ratio": "Overburden Ratio",
    "proved_reserve_mt": "Proved Reserve",
    "inferred_reserve_mt": "Inferred Reserve",
    "grade": "Coal Grade",
    "seam_name": "Seam Name",
    "depth_m": "Seam Depth",
    "district": "District",
    "block": "Block",
    "report_date": "Report Date",
    "production_mtpa": "Production (MTPA)",
    "closure_rate": "Closure Rate",
    "area_sqkm": "Block Area",
}

# Patterns used by extraction_service to find values in page text.
# Each: regex with a capture group for the numeric/grade value.
FIELD_PATTERNS = {
    "gcv": r"G(?:ross )?C(?:alorific )?V(?:alue)?[:\s]*([0-9][0-9,\.]*)\s*(kcal/kg|Kcal/kg|kCal)",
    "ash_content": r"(?:Ash|ash|मात्रा)[:\s\w-]*?([0-9][0-9,\.]*)\s*%",
    "moisture": r"(?:Moisture|moisture|नमी)[:\s\w-]*?([0-9][0-9,\.]*)\s*%",
    "ob_ratio": r"(?:O(?:\/|B|B\/) ?W|[Oo]verburden)[:\s\w-]*?([0-9][0-9,\.]*)\s*:?\s*1",
    "proved_reserve_mt": r"(?:Proved|proved|सिद्ध)[:\s\w-]*?([0-9][0-9,\.]*)\s*(?:Mt|MT|mt|million tonnes|million t)",
    "inferred_reserve_mt": r"(?:Inferred|inferred)[:\s\w-]*?([0-9][0-9,\.]*)\s*(?:Mt|MT|mt|million)",
    "grade": r"(?:Grade|grade|ग्रेड)[:\s]*([A-Z][0-9]{1,2}|[MG][0-9]{1,2})",
    "seam_name": r"Seam Name[:\s]*([A-Z][\w\/\s-]{2,40}?)(?:\s|,|;|$)",
    "depth_m": r"Seam Depth[:\s]*([0-9][0-9,\.]*)\s*m",
    "district": r"District[:\s]*([A-Za-z ]+)",
    "block": r"(?:^|\n)Block:[ ]*([A-Za-z0-9 ]+)",
    "report_date": r"Report Date[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2})",
    "area_sqkm": r"(?:Area|अंकित)[\s\w]*?([0-9][0-9,\.]*)\s*(?:sq ?km|sq\.? ?km|स्क्वेयर)",
    "production_mtpa": r"Rated Production[:\s]*([0-9][0-9,\.]*)\s*MTPA",
}

# langdetect-friendly mappings for chat language detection
LANG_LEXICON = {
    "hi": ["क्या", "बताइए", "हैं", "कोयला", "गुणवत्ता", "भंडार", "ग्रेड", "में", "की", "का"],
    "en": ["coal", "reserve", "grade", "quality", "what", "report", "block", "the", "of"],
}


def is_hindi(text: str) -> bool:
    """Rough Devanagari detection — reliable enough for demo routing."""
    devanagari = sum(1 for ch in text if "ऀ" <= ch <= "ॿ")
    return devanagari > max(1, len(text) * 0.08)


def num(value: str) -> float | None:
    """Parse a numeric string (handles Indian commas) or None."""
    import re as _re
    m = _re.sub(r"[,\s]", "", str(value))
    try:
        return float(m)
    except (ValueError, TypeError):
        return None