import enum
import uuid as uuid_pkg

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base, json_type


def _uuid() -> str:
    return str(uuid_pkg.uuid4())


def uuid_pk():
    return Column(String(36), primary_key=True, default=_uuid)


class Role(enum.Enum):
    GEOLOGIST = "GEOLOGIST"
    MINISTRY_OFFICIAL = "MINISTRY_OFFICIAL"
    AUDITOR = "AUDITOR"


class User(Base):
    __tablename__ = "users"

    id = uuid_pk()
    name = Column(String(120), nullable=False)
    role = Column(Enum(Role, name="role"), nullable=False)
    title = Column(String(160), default="")
    subsidiary = Column(String(40), default="")
    avatar_color = Column(String(9), default="#0B1B2B")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    credential = relationship("AuthCredential", back_populates="user", uselist=False,
                              cascade="all, delete-orphan")


class Coalfield(Base):
    __tablename__ = "coalfields"

    id = uuid_pk()
    name = Column(String(80), nullable=False, unique=True)
    subsidiary = Column(String(40), nullable=False)
    state = Column(String(40), nullable=False)
    area_sqkm = Column(Float, default=0)
    reserve_mt = Column(Float, default=0)
    baseline_gcv = Column(Float, default=0)
    baseline_ash = Column(Float, default=0)
    baseline_ob_ratio = Column(Float, default=0)


class DocStatus(enum.Enum):
    UPLOADING = "UPLOADING"
    OCR = "OCR"
    EXTRACTING = "EXTRACTING"
    INDEXING = "INDEXING"
    REPORTING = "REPORTING"
    READY = "READY"
    FAILED = "FAILED"


class DocCategory(enum.Enum):
    PROSPECTING = "PROSPECTING"
    GEOLOGICAL_REPORT = "GEOLOGICAL_REPORT"
    PRODUCTION = "PRODUCTION"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    RESERVES = "RESERVES"


class DocSource(enum.Enum):
    PDF = "PDF"
    SCAN = "SCAN"
    IMAGE = "IMAGE"
    SPREADSHEET = "SPREADSHEET"


class Document(Base):
    __tablename__ = "documents"

    id = uuid_pk()
    title = Column(String(240), nullable=False)
    category = Column(Enum(DocCategory, name="doc_category"), nullable=False)
    coalfield_id = Column(String(36), ForeignKey("coalfields.id"))
    block_name = Column(String(120), default="")
    district = Column(String(80), default="")
    source_type = Column(Enum(DocSource, name="doc_source"), default="PDF")
    status = Column(Enum(DocStatus, name="doc_status"), default=DocStatus.UPLOADING)
    ingestion_progress = Column(json_type(), default=dict)
    page_count = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    file_path = Column(Text, default="")
    pages_dir = Column(Text, default="")
    total_confidence = Column(Float, default=0)
    report_date = Column(String(20), default="")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    coalfield = relationship("Coalfield", backref="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    fields = relationship("FieldExtraction", back_populates="document", cascade="all, delete-orphan")
    emissions = relationship("TextEmission", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = uuid_pk()
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(Text, default="")
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    text = Column(Text, default="")          # full plain text of the page
    ocr_conf_mean = Column(Float, default=0)

    document = relationship("Document", back_populates="pages")
    emissions = relationship("TextEmission", back_populates="page", cascade="all, delete-orphan")


class TextEmission(Base):
    """Line-level text layer — THE traceability atom."""

    __tablename__ = "text_emissions"

    id = uuid_pk()
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=False)
    line_no = Column(Integer, default=0)
    text = Column(Text, default="")
    bbox = Column(json_type(), default=dict)   # normalized 0..1 {x0,y0,x1,y1}
    confidence = Column(Float, default=0)
    char_start = Column(Integer, default=0)
    char_end = Column(Integer, default=0)
    is_heading = Column(Integer, default=0)

    page = relationship("DocumentPage", back_populates="emissions")
    document = relationship("Document", back_populates="emissions")


class FieldExtraction(Base):
    __tablename__ = "field_extractions"

    id = uuid_pk()
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=False)
    page_number = Column(Integer, default=0)
    field_key = Column(String(60), nullable=False)
    field_label = Column(String(120), default="")
    value = Column(String(120), default="")
    unit = Column(String(20), default="")
    numeric_value = Column(Float, nullable=True)
    confidence = Column(Float, default=0)
    bbox = Column(json_type(), default=dict)
    matched_text = Column(Text, default="")
    method = Column(String(20), default="rule")

    document = relationship("Document", back_populates="fields")
    page = relationship("DocumentPage")