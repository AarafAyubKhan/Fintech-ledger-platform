"""
FinSight AI — Feedback Model
User feedback on reports and agent responses.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    report_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("reports.id"), nullable=True
    )
    message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Rating (1-5 stars)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Specific feedback categories
    accuracy_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_quality: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="feedback")
    report = relationship("Report", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, rating={self.rating})>"
