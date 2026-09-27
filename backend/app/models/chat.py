import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base, json_type
from app.models.document import uuid_pk


class ChatRole(enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = uuid_pk()
    title = Column(String(240), default="New query")
    language = Column(String(8), default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    __mapper_args__ = {"confirm_deleted_rows": False}


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = uuid_pk()
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Enum(ChatRole, name="chat_role"), default=ChatRole.USER)
    content = Column(Text, default="")
    language = Column(String(8), default="en")
    mode = Column(String(12), default="text")   # text | voice
    confidence = Column(Float, default=0)
    response_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
    citations = relationship("ChatCitation", back_populates="message", cascade="all, delete-orphan")


class ChatCitation(Base):
    __tablename__ = "chat_citations"

    id = uuid_pk()
    message_id = Column(String(36), ForeignKey("chat_messages.id"), nullable=False)
    rank = Column(Integer, default=0)
    snippet = Column(Text, default="")
    document_id = Column(String(36))
    page_number = Column(Integer, default=0)
    bbox = Column(json_type(), default=dict)
    char_start = Column(Integer, default=0)
    char_end = Column(Integer, default=0)
    score = Column(Float, default=0)
    document_title = Column(Text, default="")

    message = relationship("ChatMessage", back_populates="citations")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = uuid_pk()
    actor_role = Column(String(40), default="")
    action = Column(String(120), default="")
    subject = Column(Text, default="")
    at = Column(DateTime(timezone=True), server_default=func.now())