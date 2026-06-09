"""
FinSight AI — Conversation & Message Models
Tracks chat conversations with agent execution state.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="New Conversation")
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False
    )

    # Agent execution state (LangGraph checkpoint)
    agent_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    agent_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Stats
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Agent metadata (which agent generated this, what sources were used)
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Execution trace
    execution_steps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, conv={self.conversation_id})>"
