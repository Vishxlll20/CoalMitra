from sqlalchemy import Column, Date, DateTime, Float, Integer, func

from app.core.database import Base
from app.models.document import uuid_pk


class MetricSnapshot(Base):
    """Quarterly snapshot of the four headline KPIs + volume."""

    __tablename__ = "metric_snapshots"

    id = uuid_pk()
    captured_on = Column(Date, nullable=False)
    prep_time_min = Column(Float, default=0)
    extraction_accuracy = Column(Float, default=0)
    automation_pct = Column(Float, default=0)
    query_resolution_pct = Column(Float, default=0)
    docs_processed = Column(Integer, default=0)
    docs_total = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())