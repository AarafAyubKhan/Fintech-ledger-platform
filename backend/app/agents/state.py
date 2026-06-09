"""
FinSight AI — Agent State Schema
Typed state definition shared across all agents in the LangGraph workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Annotated

from langgraph.graph.message import add_messages


class AgentStep(str, Enum):
    """Track which agent is currently executing."""
    PLANNER = "planner"
    FINANCIAL_RESEARCH = "financial_research"
    REGULATORY = "regulatory"
    MARKET_INTEL = "market_intel"
    ANALYSIS = "analysis"
    VERIFICATION = "verification"
    REPORT_GENERATION = "report_generation"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class SubTask:
    """A subtask created by the planner agent."""
    id: str
    description: str
    agent: str
    status: str = "pending"
    result: str = ""


@dataclass
class Citation:
    """A citation reference for grounding."""
    source: str
    page: int | None = None
    chunk_id: str | None = None
    content_preview: str = ""
    relevance_score: float = 0.0


@dataclass
class RetrievedDocument:
    """A document chunk retrieved from the knowledge base."""
    content: str
    source: str
    page_number: int | None = None
    document_id: str = ""
    chunk_id: str = ""
    document_type: str = ""
    company: str = ""
    relevance_score: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class FinancialMetric:
    """A calculated financial metric."""
    name: str
    value: float
    unit: str = ""
    period: str = ""
    source: str = ""
    trend: str = ""  # up, down, stable


@dataclass
class VerificationResult:
    """Result from the verification agent."""
    is_verified: bool
    confidence_score: float
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    ungrounded_claims: list[str] = field(default_factory=list)


@dataclass
class ExecutionStep:
    """A record of agent execution for traceability."""
    agent_name: str
    status: str
    message: str
    data: dict | None = None
    timestamp: str = ""
    duration_ms: int = 0


class AgentState:
    """
    Typed state for the LangGraph multi-agent workflow.
    
    This state is passed between all agents and accumulates context,
    retrieved documents, analysis results, and the final report.
    """

    def __init__(
        self,
        query: str = "",
        conversation_id: str = "",
        user_id: str = "",
        companies: list[str] | None = None,
        include_regulations: bool = True,
        include_market_data: bool = True,
        generate_report: bool = False,
        # Planner output
        plan: list[dict] | None = None,
        subtasks: list[dict] | None = None,
        # Retrieved context
        financial_context: list[dict] | None = None,
        regulatory_context: list[dict] | None = None,
        market_context: list[dict] | None = None,
        # Analysis
        analysis_results: dict | None = None,
        financial_metrics: list[dict] | None = None,
        # Verification
        verification_status: dict | None = None,
        # Citations
        citations: list[dict] | None = None,
        # Report
        answer: str = "",
        report: dict | None = None,
        report_id: str | None = None,
        # Execution tracking
        current_step: str = "planner",
        execution_steps: list[dict] | None = None,
        errors: list[str] | None = None,
        total_tokens: int = 0,
    ):
        self.query = query
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.companies = companies or []
        self.include_regulations = include_regulations
        self.include_market_data = include_market_data
        self.generate_report = generate_report
        self.plan = plan or []
        self.subtasks = subtasks or []
        self.financial_context = financial_context or []
        self.regulatory_context = regulatory_context or []
        self.market_context = market_context or []
        self.analysis_results = analysis_results or {}
        self.financial_metrics = financial_metrics or []
        self.verification_status = verification_status or {}
        self.citations = citations or []
        self.answer = answer
        self.report = report or {}
        self.report_id = report_id
        self.execution_steps = execution_steps or []
        self.errors = errors or []
        self.total_tokens = total_tokens
        self.current_step = current_step

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "companies": self.companies,
            "include_regulations": self.include_regulations,
            "include_market_data": self.include_market_data,
            "generate_report": self.generate_report,
            "plan": self.plan,
            "subtasks": self.subtasks,
            "financial_context": self.financial_context,
            "regulatory_context": self.regulatory_context,
            "market_context": self.market_context,
            "analysis_results": self.analysis_results,
            "financial_metrics": self.financial_metrics,
            "verification_status": self.verification_status,
            "citations": self.citations,
            "answer": self.answer,
            "report": self.report,
            "report_id": self.report_id,
            "current_step": self.current_step,
            "execution_steps": self.execution_steps,
            "errors": self.errors,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentState":
        return cls(**data)


# LangGraph-compatible TypedDict state
from typing import TypedDict


class GraphState(TypedDict, total=False):
    """LangGraph-compatible state definition."""
    query: str
    conversation_id: str
    user_id: str
    companies: list[str]
    include_regulations: bool
    include_market_data: bool
    generate_report: bool
    plan: list[dict]
    subtasks: list[dict]
    financial_context: list[dict]
    regulatory_context: list[dict]
    market_context: list[dict]
    analysis_results: dict
    financial_metrics: list[dict]
    verification_status: dict
    citations: list[dict]
    answer: str
    report: dict
    report_id: str
    current_step: str
    execution_steps: list[dict]
    errors: list[str]
    total_tokens: int
