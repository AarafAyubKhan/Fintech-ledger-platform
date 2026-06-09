"""Initial migration — all core tables

Revision ID: 001_initial
Create Date: 2025-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=True),
        sa.Column(
            "role",
            sa.Enum("user", "analyst", "admin", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "oauth_provider",
            sa.Enum("local", "google", name="oauthprovider"),
            nullable=False,
            server_default="local",
        ),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── Companies ─────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("ticker", sa.String(20), nullable=True, unique=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("exchange", sa.String(20), nullable=True),
        sa.Column("market_cap", sa.Float, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("financial_data", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── Regulations ───────────────────────────────────────────
    op.create_table(
        "regulations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=True, unique=True),
        sa.Column("issuer", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("effective_date", sa.Date, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("full_text", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── Documents ─────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column(
            "file_type",
            sa.Enum("pdf", "docx", "txt", "html", name="filetype"),
            nullable=False,
        ),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False),
        sa.Column(
            "document_type",
            sa.Enum(
                "annual_report",
                "quarterly_report",
                "earnings_transcript",
                "regulatory",
                "research_report",
                "news",
                "other",
                name="documenttype",
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="documentstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("regulation_id", sa.String(36), sa.ForeignKey("regulations.id"), nullable=True),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=True),
        sa.Column("processing_error", sa.Text, nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_status", "documents", ["status"])

    # ── Document Chunks ───────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("char_count", sa.Integer, nullable=True),
        sa.Column("qdrant_point_id", sa.String(36), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("chunk_metadata", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])

    # ── Conversations ─────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False, server_default="New Conversation"),
        sa.Column(
            "status",
            sa.Enum("active", "archived", "deleted", name="conversationstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("message_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("agent_state", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    # ── Messages ──────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", name="messagerole"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=True),
        sa.Column("citations", JSONB, nullable=True),
        sa.Column("execution_steps", JSONB, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # ── Reports ───────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False, server_default="equity_research"),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("key_findings", sa.Text, nullable=True),
        sa.Column("detailed_analysis", sa.Text, nullable=True),
        sa.Column("opportunities", sa.Text, nullable=True),
        sa.Column("risks", sa.Text, nullable=True),
        sa.Column("regulatory_impact", sa.Text, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("companies", JSONB, nullable=True),
        sa.Column("citations", JSONB, nullable=True),
        sa.Column("financial_metrics", JSONB, nullable=True),
        sa.Column("charts_data", JSONB, nullable=True),
        sa.Column("word_count", sa.Integer, nullable=True),
        sa.Column("source_count", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_reports_user_id", "reports", ["user_id"])

    # ── Feedback ──────────────────────────────────────────────
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("message_id", sa.String(36), nullable=True),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("accuracy_rating", sa.Float, nullable=True),
        sa.Column("relevance_rating", sa.Float, nullable=True),
        sa.Column("citation_quality", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── Audit Logs ────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("details", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    # ── Knowledge Graph Entities ──────────────────────────────
    op.create_table(
        "kg_entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("properties", JSONB, server_default="{}"),
        sa.Column("source_documents", JSONB, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_kg_entities_name_type", "kg_entities", ["name", "entity_type"], unique=True
    )

    # ── Knowledge Graph Relationships ─────────────────────────
    op.create_table(
        "kg_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), nullable=False, index=True),
        sa.Column("target_id", sa.String(36), nullable=False, index=True),
        sa.Column("relationship_type", sa.String(100), nullable=False, index=True),
        sa.Column("properties", JSONB, server_default="{}"),
        sa.Column("source_documents", JSONB, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_kg_rels_source_target_type",
        "kg_relationships",
        ["source_id", "target_id", "relationship_type"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("kg_relationships")
    op.drop_table("kg_entities")
    op.drop_table("audit_logs")
    op.drop_table("feedback")
    op.drop_table("reports")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("regulations")
    op.drop_table("companies")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS oauthprovider")
    op.execute("DROP TYPE IF EXISTS filetype")
    op.execute("DROP TYPE IF EXISTS documenttype")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS conversationstatus")
    op.execute("DROP TYPE IF EXISTS messagerole")
