import enum

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, Text, func

from app.core.database import Base, json_type
from app.models.document import uuid_pk


class ReportStatus(enum.Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"


class Report(Base):
    __tablename__ = "reports"

    id = uuid_pk()
    document_id = Column(String(36), unique=False)
    title = Column(String(240), default="")
    template_type = Column(String(60), default="standard")
    sections = Column(json_type(), default=list)       # ordered [narrative|table] blocks
    narrative = Column(json_type(), default=dict)      # summary narrative object
    metrics = Column(json_type(), default=dict)
    role = Column(String(40), default="GEOLOGIST")
    status = Column(Enum(ReportStatus, name="report_status"), default=ReportStatus.DRAFT)
    pdf_path = Column(Text, default="")
    source_count = Column(Integer, default=0)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())


class AnomalySeverity(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyStatus(enum.Enum):
    OPEN = "OPEN"
    REVIEWED = "REVIEWED"


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = uuid_pk()
    document_id = Column(String(36))
    coalfield_id = Column(String(36))
    block_name = Column(String(120), default="")
    metric_key = Column(String(40), nullable=False)
    label = Column(String(120), default="")
    expected_value = Column(String(40), default="")
    actual_value = Column(String(40), default="")
    deviation_pct = Column(Float, default=0)
    severity = Column(Enum(AnomalySeverity, name="anomaly_severity"), default=AnomalySeverity.LOW)
    status = Column(Enum(AnomalyStatus, name="anomaly_status"), default=AnomalyStatus.OPEN)
    rationale = Column(Text, default="")
    page_number = Column(Integer, default=0)
    bbox = Column(json_type(), default=dict)
    confidence = Column(Float, default=0)
    baseline_document_id = Column(String(36), default="")
    detected_at = Column(DateTime(timezone=True), server_default=func.now())