"""AI answer generation — pluggable provider.

* OpenAIProvider  — real LLM grounding (DEMO_MODE=0 + OPENAI_API_KEY).
* TemplateResponder — deterministic, retrieval-grounded "official response"
  composer that works offline. Slot-fills retrieved chunks into a formal
  CMPDI-style reply with an inline citation list and a confidence figure.

Both return the same shape: {reply, confidence, citations:[]}.
"""
from __future__ import annotations

import re

from app.core.config import settings
from app.utils.text import is_hindi

HI_TEMPLATE = (
    "माननीय महोदय, आपके प्रश्नोत्तर के आधार पर, उपलब्ध प्रलेखों (पृष्ठ {pages}) के "
    "अनुसार {answer_part}।{cite_part} यह उत्तर मूल दस्तावेज़ों की अवधारण स्थिति के आधार पर है."
)

HI_CITE = " इसका स्रोत {refs} द्वारा सत्यापित किया जा सकता है।"


class _Citation:
    def __init__(self, doc_id="", title="", page=1, bbox=None, snippet="", score=0.0,
                 char_start=0, char_end=40):
        self.document_id = doc_id
        self.title = title
        self.page_number = page
        self.bbox = bbox or {}
        self.snippet = snippet
        self.score = score
        self.char_start = char_start
        self.char_end = char_end

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "page_number": self.page_number,
            "bbox": self.bbox,
            "snippet": self.snippet[:300],
            "score": round(self.score, 3),
            "char_start": self.char_start,
            "char_end": self.char_end,
        }


class OpenAIProvider:
    """Real LLM path (used only when configured)."""

    def __init__(self):
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=settings.openai_api_key)

    def answer(self, question: str, context_chunks: list[dict], lang: str) -> dict:
        ctx = "\n\n".join(
            f"[Doc: {c.get('title')} page {c.get('page_number')}] {c.get('source')}"[:900]
            for c in context_chunks
        )
        prompt = (
            "Answer in official administrative English (or Hindi if requested) as a CMPDI "
            "geological report officer. Ground every claim in the context. End with "
            "[Sources: ...] listing document & page.\n\n" + ctx + "\n\nQ: " + question
        )
        reply = self.llm.invoke(prompt).content
        citations = [
            _Citation(
                doc_id=c.get("document_id", ""),
                title=c.get("title", ""),
                page=c.get("page_number", 1),
                bbox=c.get("bbox"),
                snippet=c.get("source", ""),
                score=c.get("score", 0.8),
            )
            for c in context_chunks[:4]
        ]
        conf = min(0.96, 0.7 + 0.05 * len(context_chunks))
        return {"reply": reply, "confidence": round(conf, 2), "citations": [c.to_dict() for c in citations]}


class TemplateResponder:
    """Deterministic, offline, retrieval-grounded official response."""

    def __init__(self, questions_db=None):
        self.questions_db = questions_db  # optional QA template DB for demo-mode Q&A

    def answer(self, question: str, context_chunks: list[dict], lang: str) -> dict:
        """Build an official-response answer from retrieved chunks."""
        top = context_chunks[:3]
        citations = [_Citation(
            doc_id=c.get("document_id", ""),
            title=c.get("title") or "Source document",
            page=c.get("page_number", 1),
            bbox=c.get("bbox"),
            snippet=c.get("source", ""),
            score=c.get("score", 0.0),
            char_start=c.get("char_start", 0),
            char_end=c.get("char_end", 300),
        ) for c in top]

        # Compose the factual core from the best chunk(s)
        facts = []
        for c in top:
            snippet = re.sub(r"\s+", " ", c.get("source", "")).strip()[:220]
            facts.append(
                f"Document «{c.get('title') or 'source'}», page {c.get('page_number', 1)} "
                f"states: “{snippet}…”"
            )

        cite_part = ""
        pages = ", ".join(str(c.page_number) for c in citations)
        refs = ", ".join(f"{c.title} (पृष्ठ {c.page_number})" for c in citations[:2])

        if lang == "hi" and is_hindi(question):
            answer_part = (
                "प्रचलित प्रलेखों से स्पष्ट है कि — " + " ; ".join(
                    f"{c.title or 'स्रोत'} पृष्ठ {c.page_number} पर उल्लिखित है: “{re.sub(r'[^ऀ-ॿ\w .,:;]', '', c.get('source', ''))[:180]}…”"
                    for c in top[:2]
                )
            )
            cite_line = HI_CITE.format(refs=refs) if citations else ""
            reply = HI_TEMPLATE.format(
                pages=pages or "—", answer_part=answer_part, cite_part=cite_line
            )
        else:
            base = (
                "In response to your query, the consolidated records establish the following. "
                + " ".join(facts)
            )
            if citations:
                base += " The figures above are directly traceable to the cited source pages."
            reply = base

        confidence = round(max(0, min(0.96, 0.62 + 0.09 * len(citations))), 2)
        return {"reply": reply, "confidence": confidence, "citations": [c.to_dict() for c in citations]}


def get_answerer():
    """Resolve the right answerer for the current config."""
    if not settings.demo_mode:
        lookup = _try_real_llm()
        if lookup:
            return lookup
    return TemplateResponder()


def _try_real_llm():
    if settings.openai_api_key:
        try:
            return OpenAIProvider()
        except Exception:
            return None
    return None


def demo_qa(question: str, corpus: list[dict], lang: str) -> dict:
    """Deterministic demo Q&A used when no RAG index or answerer is reachable.

    corpus: list of {document_id, title, page_number, bbox, text}
    Picks the best-matching doc by phrase score and returns a grounded reply.
    """
    q = question.lower()
    best = None
    best_score = 0
    for d in corpus:
        hay = (d.get("title", "") + " " + d.get("text", "")).lower()
        score = sum(hay.count(w.lower()) for w in (q.split() if " " in q else [q]))
        if score > best_score:
            best_score = score
            best = d
    if best is None or best_score == 0:
        return {
            "reply": ("उपलब्ध प्रलेखों में से कोई सटीक मिलान नहीं मिला। कृपया किसी खंड, सीम, "
                      "या ग्रेड का नाम लिखें।") if is_hindi(question) else
                     "No matching record found in the available corpus. Please name a block, seam, or grade.",
            "confidence": 0.12,
            "citations": [],
        }
    c = _Citation(
        doc_id=best["document_id"],
        title=best["title"],
        page=best.get("page_number", 1),
        bbox=best.get("bbox"),
        snippet=best.get("text", "")[:300],
        score=round(best_score * 0.25, 3),
    )
    snippet = re.sub(r"\s+", " ", best.get("text", "")).strip()[:220]
    if is_hindi(question):
        reply = (
            f"उपलब्ध प्रलेख «{best['title']}» पृष्ठ {best.get('page_number', 1)} के अनुसार — {snippet}… "
            f"यह उत्तर स्रोत पृष्ठ से जुड़ा हुआ है (अद्यतनांक देखने के लिए पृष्ठ पर क्लिक करें)।"
        )
    else:
        reply = (
            f"Based on available records, <{best['title']}> (page {best.get('page_number', 1)}) "
            f"reports: “{snippet}…”. This answer links directly to the source page for verification."
        )
    return {"reply": reply, "confidence": 0.52, "citations": [c.to_dict()]}