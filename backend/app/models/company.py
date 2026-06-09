"""
FinSight AI — Company Model
Tracks companies referenced in financial documents.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ticker: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Financial snapshot (latest known)
    financial_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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
    documents = relationship("Document", back_populates="company", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, ticker={self.ticker})>"
