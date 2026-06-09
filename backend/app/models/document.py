"""
FinSight AI — Document & Chunk Models
Tracks uploaded documents and their processed chunks with metadata.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_REPORT = "quarterly_report"
    EARNINGS_TRANSCRIPT = "earnings_transcript"
    REGULATORY_CIRCULAR = "regulatory_circular"
    NEWS_ARTICLE = "news_article"
    RESEARCH_REPORT = "research_report"
    FINANCIAL_STATEMENT = "financial_statement"
    OTHER = "other"


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), default=DocumentType.OTHER, nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False
    )

    # Metadata
    company_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("companies.id"), nullable=True
    )
    regulation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("regulations.id"), nullable=True
    )
    uploaded_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Processing info
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    company = relationship("Company", back_populates="documents")
    regulation = relationship("Regulation", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Embedding info
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Extracted metadata for this chunk
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, doc={self.document_id}, index={self.chunk_index})>"
