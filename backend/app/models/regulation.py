"""
FinSight AI — Regulation Model
Tracks RBI circulars, SEBI notifications, and banking regulations.
"""

import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RegulationIssuer(str, enum.Enum):
    RBI = "rbi"
    SEBI = "sebi"
    IRDAI = "irdai"
    OTHER = "other"


class RegulationCategory(str, enum.Enum):
    MONETARY_POLICY = "monetary_policy"
    BANKING_REGULATION = "banking_regulation"
    MARKET_REGULATION = "market_regulation"
    COMPLIANCE = "compliance"
    CONSUMER_PROTECTION = "consumer_protection"
    OTHER = "other"


class Regulation(Base):
    __tablename__ = "regulations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    issuer: Mapped[RegulationIssuer] = mapped_column(
        Enum(RegulationIssuer), nullable=False
    )
    category: Mapped[RegulationCategory] = mapped_column(
        Enum(RegulationCategory), default=RegulationCategory.OTHER, nullable=False
    )
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    documents = relationship("Document", back_populates="regulation", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Regulation(id={self.id}, title={self.title}, issuer={self.issuer})>"
