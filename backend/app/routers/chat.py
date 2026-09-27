from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DocumentPage, TextEmission
from app.models.chat import ChatCitation, ChatMessage as ChatMsg, ChatRole, ChatSession
from app.utils.text import is_hindi

router = APIRouter(tags=["chat"])


def _citation_ser(c: ChatCitation) -> dict:
    return {
        "id": c.id,
        "rank": c.rank,
        "snippet": c.snippet,
        "document_id": c.document_id,
        "document_title": c.document_title or "",
        "page_number": c.page_number,
        "bbox": c.bbox or {},
        "score": c.score or 0,
    }


def _message_payload(m: ChatMsg, citations=None) -> dict:
    # Frontend expects lowercase "user"/"assistant"
    role_val = m.role.value if m.role else "USER"
    role_map = {"USER": "user", "SYSTEM": "assistant"}
    return {
        "id": m.id,
        "role": role_map.get(role_val, role_val.lower()),
        "content": m.content,
        "language": m.language or "en",
        "mode": m.mode or "text",
        "confidence": m.confidence or 0,
        "response_ms": m.response_ms or 0,
        "citations": citations or [],
    }


def _collect_corpus(db) -> list[dict]:
    """Corpus of page texts for demo retrieval (used when no index)."""
    from app.models import Document
    docs = db.query(Document).all()
    out = []
    for d in docs:
        pages = (
            db.query(DocumentPage)
            .filter(DocumentPage.document_id == d.id)
            .order_by(DocumentPage.page_number)
            .all()
        )
        for p in pages:
            emissions = (
                db.query(TextEmission)
                .filter(TextEmission.page_id == p.id)
                .order_by(TextEmission.line_no)
                .all()
            )
            box = next((e.bbox for e in emissions if e.bbox), {})
            text = p.text or " ".join(e.text for e in emissions)
            if text.strip():
                out.append({
                    "document_id": d.id,
                    "title": d.title,
                    "block": d.block_name,
                    "coalfield": d.coalfield.name if d.coalfield else "",
                    "page_number": p.page_number,
                    "bbox": box,
                    "text": text,
                })
    return out


@router.post("/chat/sessions")
def create_session(payload: dict | None = None, db: Session = Depends(get_db)):
    title = (payload or {}).get("title") or "New query"
    s = ChatSession(title=title, language="en")
    db.add(s)
    db.commit()
    return {"id": s.id, "title": s.title, "language": s.language}


@router.get("/chat/sessions")
def list_sessions(db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = (
        db.query(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [{"id": s.id, "title": s.title, "language": s.language} for s in rows]


@router.get("/chat/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMsg)
        .filter(ChatMsg.session_id == session_id)
        .order_by(ChatMsg.created_at.asc())
        .all()
    )
    result = []
    for m in rows:
        citations = []
        if m.role == ChatRole.SYSTEM:
            citations = [
                _citation_ser(c)
                for c in db.query(ChatCitation).filter(ChatCitation.message_id == m.id).all()
            ]
        result.append(_message_payload(m, citations))
    return result


def _answer(question: str, lang: str, db: Session) -> dict:
    """Retrieve context and compose an answer with citations."""
    from app.services.index_service import keyword_search
    corpus = _collect_corpus(db)

    # Try chroma first (real path), fall back to deterministic keyword search
    retrieved = []
    try:
        from app.services.index_service import get_collection
        col = get_collection()
        if col and col.count() > 0:
            hits = col.query(query_texts=[question], n_results=4)
            for i in range(len(hits.get("ids", [[]])[0])):
                doc = hits["documents"][0][i]
                meta = hits["metadatas"][0][i]
                retrieved.append({
                    "document_id": meta.get("document_id"),
                    "title": meta.get("title", ""),
                    "page_number": int(meta.get("page_number", 1)),
                    "bbox": meta.get("bbox"),
                    "source": doc,
                    "score": 1.0 - float(hits.get("distances", [[0]])[0][i]),
                    "char_start": int(meta.get("char_start", 0)),
                    "char_end": int(meta.get("char_end", 300)),
                })
    except Exception:
        retrieved = keyword_search(question, corpus[:60], top_k=3)

    if not retrieved:
        from app.services.answerer import demo_qa
        return demo_qa(question, corpus[:60], lang)

    from app.services.answerer import get_answerer
    answerer = get_answerer()
    return answerer.answer(question, retrieved, lang)


def _run_query(question: str, lang: str, session_id: str, mode: str, db: Session) -> dict:
    """Shared logic for text and voice queries. Returns a ChatMessage payload."""
    t0 = time.time()
    s = db.query(ChatSession).get(session_id)
    if s is None:
        raise HTTPException(404, "Session not found")

    result = _answer(question, lang, db)
    ms = int((time.time() - t0) * 1000)

    user_msg = ChatMsg(session_id=session_id, role=ChatRole.USER, content=question,
                       language=lang, mode=mode)
    db.add(user_msg)
    db.flush()

    sys_msg = ChatMsg(session_id=session_id, role=ChatRole.SYSTEM,
                      content=result["reply"], language=lang,
                      confidence=result["confidence"], response_ms=ms, mode=mode)
    db.add(sys_msg)
    db.flush()

    for rank, c in enumerate(result["citations"]):
        db.add(ChatCitation(
            message_id=sys_msg.id,
            rank=rank,
            snippet=c.get("snippet", ""),
            document_id=c.get("document_id", ""),
            page_number=c.get("page_number", 1),
            bbox=c.get("bbox"),
            char_start=c.get("char_start", 0),
            char_end=c.get("char_end", 300),
            score=c.get("score", 0),
            document_title=c.get("title", ""),
        ))
    db.commit()

    citations = [
        _citation_ser(c)
        for c in db.query(ChatCitation).filter(ChatCitation.message_id == sys_msg.id).all()
    ]

    return _message_payload(sys_msg, citations)


@router.post("/chat/sessions/{session_id}/query")
def chat_query(session_id: str, payload: dict, db: Session = Depends(get_db)):
    question = (payload.get("text") or payload.get("question") or "").strip()
    lang = (payload.get("language") or payload.get("lang") or "auto")[:2]

    if not question:
        raise HTTPException(400, "Empty question")

    if lang == "auto":
        lang = "hi" if is_hindi(question) else "en"

    return _run_query(question, lang, session_id, "text", db)


@router.post("/chat/sessions/{session_id}/voice")
async def chat_voice(
    session_id: str,
    audio: UploadFile = File(...),
    language: str = Form("auto"),
    db: Session = Depends(get_db),
):
    audio_data = await audio.read()
    if not audio_data:
        raise HTTPException(400, "Empty audio payload")

    from app.services.transcribe_service import transcribe
    result = transcribe(audio_data, sample_rate=16000)
    question = result["transcript"]
    detected = result["language"]
    if language == "auto":
        language = detected

    return _run_query(question, language, session_id, "voice", db)


# Legacy endpoints kept for backward compatibility
@router.post("/chat/query")
def chat_query_legacy(payload: dict, db: Session = Depends(get_db)):
    question = (payload.get("question") or "").strip()
    lang = (payload.get("lang") or "auto")[:2]
    session_id = payload.get("session_id")
    mode = payload.get("mode", "text")

    if not question:
        raise HTTPException(400, "Empty question")

    if lang == "auto" or "lang" not in payload:
        lang = "hi" if is_hindi(question) else "en"

    if not session_id:
        s = ChatSession(title=question[:60], language=lang)
        db.add(s)
        db.flush()
        session_id = s.id

    msg = _run_query(question, lang, session_id, mode, db)
    return {"session_id": session_id, "system_message": msg}
