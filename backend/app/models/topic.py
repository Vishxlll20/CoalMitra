from sqlalchemy import Column, Float, ForeignKey, Integer, String

from app.core.database import Base
from app.models.document import uuid_pk


class Topic(Base):
    __tablename__ = "topics"

    id = uuid_pk()
    key = Column(String(60), nullable=False, unique=True)
    label = Column(String(120), nullable=False)
    color = Column(String(9), default="#E8A33D")


class DocumentTopic(Base):
    __tablename__ = "document_topics"

    id = uuid_pk()
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    weight = Column(Float, default=0)
    quarter = Column(String(8), default="")


class DocumentWord(Base):
    __tablename__ = "doc_word_stats"

    id = uuid_pk()
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    word = Column(String(120), nullable=False)
    count = Column(Integer, default=0)
    tfidf = Column(Float, default=0)


class QuantMetric(Base):
    """Per-document numeric quality metric used by reports + anomaly service."""

    __tablename__ = "quant_metrics"

    id = uuid_pk()
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    metric_key = Column(String(40), nullable=False)
    label = Column(String(120), default="")
    value = Column(Float, default=0)
    unit = Column(String(20), default="")
    conf = Column(Float, default=0)