"""Import every model so Base.metadata sees all tables."""
from app.models.auth import AuthChatSession, AuthCredential, AuthSession
from app.models.chat import AuditEvent, ChatCitation, ChatMessage, ChatSession
from app.models.document import (
    Coalfield,
    DocCategory,
    DocSource,
    DocStatus,
    Document,
    DocumentPage,
    FieldExtraction,
    Role,
    TextEmission,
    User,
)
from app.models.metric import MetricSnapshot
from app.models.report import Anomaly, Report, ReportStatus
from app.models.topic import DocumentTopic, DocumentWord, QuantMetric, Topic

__all__ = [
    "AuditEvent",
    "AuthChatSession",
    "AuthCredential",
    "AuthSession",
    "ChatCitation",
    "ChatMessage",
    "ChatSession",
    "Coalfield",
    "DocCategory",
    "DocSource",
    "DocStatus",
    "Document",
    "DocumentPage",
    "DocumentTopic",
    "DocumentWord",
    "FieldExtraction",
    "MetricSnapshot",
    "QuantMetric",
    "Report",
    "Role",
    "TextEmission",
    "Topic",
    "User",
]