"""
FinSight AI — Pydantic Schemas
Request/response validation models for all API endpoints.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# ═══════════════════════════════════════════════════════════════
# Auth Schemas
# ═══════════════════════════════════════════════════════════════


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ═══════════════════════════════════════════════════════════════
# User Schemas
# ═══════════════════════════════════════════════════════════════


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(user|analyst|admin)$")


# ═══════════════════════════════════════════════════════════════
# Document Schemas
# ═══════════════════════════════════════════════════════════════


class DocumentResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    file_name: str
    file_type: str
    file_size_bytes: int
    document_type: str
    status: str
    company_id: str | None = None
    page_count: int | None = None
    chunk_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    document_type: str = "other"
    company_id: str | None = None
    regulation_id: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# Conversation Schemas
# ═══════════════════════════════════════════════════════════════


class CreateConversationRequest(BaseModel):
    title: str | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    status: str
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CitationSchema(BaseModel):
    source: str
    page: int | None = None
    chunk_id: str | None = None
    content_preview: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    agent_name: str | None = None
    citations: list[CitationSchema] | None = None
    execution_steps: list[dict] | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]


# ═══════════════════════════════════════════════════════════════
# Research Schemas
# ═══════════════════════════════════════════════════════════════


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    companies: list[str] | None = None
    include_regulations: bool = True
    include_market_data: bool = True


class CompareRequest(BaseModel):
    companies: list[str] = Field(..., min_length=2, max_length=5)
    metrics: list[str] | None = None


class PortfolioReportRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    ticker: str | None = None
    include_charts: bool = True
    include_risk_analysis: bool = True
    include_regulatory_impact: bool = True


class AgentStepResponse(BaseModel):
    agent_name: str
    status: str
    message: str
    data: dict[str, Any] | None = None
    timestamp: datetime


class ResearchResponse(BaseModel):
    id: str
    query: str
    answer: str
    citations: list[CitationSchema]
    agent_steps: list[AgentStepResponse]
    report_id: str | None = None
    latency_ms: int


# ═══════════════════════════════════════════════════════════════
# Report Schemas
# ═══════════════════════════════════════════════════════════════


class ReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    executive_summary: str | None = None
    key_findings: str | None = None
    detailed_analysis: str | None = None
    opportunities: str | None = None
    risks: str | None = None
    regulatory_impact: str | None = None
    recommendation: str | None = None
    companies: list[str] | None = None
    citations: list[CitationSchema] | None = None
    financial_metrics: dict | None = None
    charts_data: dict | None = None
    word_count: int | None = None
    source_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int


# ═══════════════════════════════════════════════════════════════
# Company Schemas
# ═══════════════════════════════════════════════════════════════


class CompanyResponse(BaseModel):
    id: str
    name: str
    ticker: str | None = None
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    market_cap: float | None = None
    description: str | None = None
    financial_data: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    ticker: str | None = None
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None


# ═══════════════════════════════════════════════════════════════
# Admin Schemas
# ═══════════════════════════════════════════════════════════════


class AdminStatsResponse(BaseModel):
    total_users: int
    total_documents: int
    total_conversations: int
    total_reports: int
    active_users_today: int
    documents_processed: int
    avg_response_time_ms: float


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Feedback Schemas
# ═══════════════════════════════════════════════════════════════


class FeedbackRequest(BaseModel):
    report_id: str | None = None
    message_id: str | None = None
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    accuracy_rating: float | None = Field(None, ge=0, le=5)
    relevance_rating: float | None = Field(None, ge=0, le=5)
    citation_quality: float | None = Field(None, ge=0, le=5)


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    report_id: str | None = None
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Health Schemas
# ═══════════════════════════════════════════════════════════════


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    services: dict[str, str]
