"""Insights: word frequencies (word cloud) + topic weighting + topic drift."""
from __future__ import annotations

import re

from app.utils.text import tokenize

TOPIC_TERMS = {
    "exploration": {"exploration", "borehole", "drilling", "prospecting", "survey", "mapping", "अन्वेषण", "ड्रिलिंग"},
    "reserves": {"reserve", "reserves", "proved", "inferred", "resource", "भंडार", "सिद्ध"},
    "seam-quality": {"seam", "grade", "gcv", "calorific", "ash", "moisture", "quality", "सीम", "गुणवत्ता", "राख"},
    "environment": {"environment", "closure", "reclamation", "emission", "forest", "water", "पर्यावरण", "पुनर्वास"},
    "production": {"production", "output", "dispatch", "mtpa", "tonnage", "उत्पादन"},
    "compliance": {"compliance", "consent", "clearance", "audit", "statutory", "safety", "अनुपालन", "स्वीकृति"},
}


def compute_word_stats(page_texts: list[str]) -> list[tuple[str, int]]:
    """Count word frequencies across a document's pages (EN + Devanagari)."""
    counts: dict[str, int] = {}
    for t in page_texts:
        for w in tokenize(t):
            counts[w] = counts.get(w, 0) + 1
    return sorted(counts.items(), key=lambda kv: -kv[1])


def infer_topic_weights(text: str, limit: int = 3) -> list[tuple[str, float]]:
    """Rank interpretable EN/HI topic keyword matches for a document's text."""
    tokens = re.findall(r"[\wऀ-ॿ]+", text.lower())
    counts = {
        topic: sum(1 for token in tokens if token in terms)
        for topic, terms in TOPIC_TERMS.items()
    }
    ranked = sorted(
        ((topic, count) for topic, count in counts.items() if count),
        key=lambda item: (-item[1], item[0]),
    )[:limit]
    if not ranked:
        return []
    maximum = ranked[0][1]
    return [(topic, round(count / maximum, 3)) for topic, count in ranked]


def top_words(word_docs: list[dict], limit: int = 120) -> list[dict]:
    """Aggregate document word stats into a global word cloud payload.

    word_docs: list of {word, count, document_id}
    Returns [{word, count, size, color_idx}] sized for a word cloud.
    """
    agg: dict[str, int] = {}
    for wd in word_docs:
        agg[wd["word"]] = agg.get(wd["word"], 0) + wd["count"]
    ranked = sorted(agg.items(), key=lambda kv: -kv[1])[:limit]
    if not ranked:
        return []
    max_c = ranked[0][1] or 1
    return [
        {
            "word": w,
            "count": c,
            "size": 12 + int(48 * (c / max_c)),
        }
        for w, c in ranked
    ]


def drift_series(document_topics: list[dict]) -> list[dict]:
    """Build [{quarter, topic, weight}] for the stacked area chart.

    document_topics: [{quarter, label, weight}]
    """
    out: list[dict] = []
    for dt in sorted(document_topics, key=lambda x: x["quarter"]):
        out.append({
            "quarter": dt["quarter"],
            "topic": dt["label"],
            "weight": round(dt["weight"], 3),
        })
    return out


