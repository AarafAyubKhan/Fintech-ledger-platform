"""
FinSight AI — Report Model
Generated research reports with citations and export capabilities.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReportFormat(str, enum.Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"


class ReportType(str, enum.Enum):
    EQUITY_RESEARCH = "equity_research"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    REGULATORY_IMPACT = "regulatory_impact"
    EARNINGS_SUMMARY = "earnings_summary"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_REPORT = "portfolio_report"
    CUSTOM = "custom"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    conversation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType), default=ReportType.CUSTOM, nullable=False
    )

    # Report content sections
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    detailed_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulatory_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    companies: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    financial_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    charts_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Export paths
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    docx_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    user = relationship("User", back_populates="reports")
    feedback = relationship("Feedback", back_populates="report", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, title={self.title}, type={self.report_type})>"
