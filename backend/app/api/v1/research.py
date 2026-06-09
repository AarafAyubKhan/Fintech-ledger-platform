"""
FinSight AI — Research Endpoints
Analyze, compare companies, and generate portfolio reports.
"""

import time

import structlog
from fastapi import APIRouter
from sqlalchemy import select
from uuid6 import uuid7

from app.api.deps import CurrentUser, DBSession
from app.models.conversation import Conversation, ConversationStatus
from app.schemas import (
    CompareRequest,
    PortfolioReportRequest,
    ResearchRequest,
    ResearchResponse,
)

router = APIRouter()
logger = structlog.get_logger()


@router.post("/analyze", response_model=ResearchResponse)
async def analyze(
    request: ResearchRequest,
    user: CurrentUser,
    db: DBSession,
) -> ResearchResponse:
    """Run a comprehensive financial analysis query through the agent pipeline."""
    start_time = time.perf_counter()

    # Create a conversation for tracking
    conversation = Conversation(
        id=str(uuid7()),
        user_id=user.id,
        title=request.query[:100],
        status=ConversationStatus.PROCESSING,
    )
    db.add(conversation)
    await db.flush()

    # Run the agent pipeline
    from app.agents.orchestrator import run_agent_pipeline

    agent_result = await run_agent_pipeline(
        query=request.query,
        conversation_id=conversation.id,
        user_id=user.id,
        db=db,
        companies=request.companies,
        include_regulations=request.include_regulations,
        include_market_data=request.include_market_data,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    conversation.status = ConversationStatus.COMPLETED

    return ResearchResponse(
        id=conversation.id,
        query=request.query,
        answer=agent_result.get("answer", ""),
        citations=agent_result.get("citations", []),
        agent_steps=agent_result.get("execution_steps", []),
        report_id=agent_result.get("report_id"),
        latency_ms=latency_ms,
    )


@router.post("/compare", response_model=ResearchResponse)
async def compare_companies(
    request: CompareRequest,
    user: CurrentUser,
    db: DBSession,
) -> ResearchResponse:
    """Compare multiple companies on financial metrics."""
    start_time = time.perf_counter()

    query = f"Compare the following companies: {', '.join(request.companies)}"
    if request.metrics:
        query += f" on these metrics: {', '.join(request.metrics)}"

    conversation = Conversation(
        id=str(uuid7()),
        user_id=user.id,
        title=f"Comparison: {' vs '.join(request.companies)}",
        status=ConversationStatus.PROCESSING,
    )
    db.add(conversation)
    await db.flush()

    from app.agents.orchestrator import run_agent_pipeline

    agent_result = await run_agent_pipeline(
        query=query,
        conversation_id=conversation.id,
        user_id=user.id,
        db=db,
        companies=request.companies,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    conversation.status = ConversationStatus.COMPLETED

    return ResearchResponse(
        id=conversation.id,
        query=query,
        answer=agent_result.get("answer", ""),
        citations=agent_result.get("citations", []),
        agent_steps=agent_result.get("execution_steps", []),
        report_id=agent_result.get("report_id"),
        latency_ms=latency_ms,
    )


@router.post("/portfolio-report", response_model=ResearchResponse)
async def generate_portfolio_report(
    request: PortfolioReportRequest,
    user: CurrentUser,
    db: DBSession,
) -> ResearchResponse:
    """
    Generate a complete equity research report (Portfolio Mode).
    This is the hero feature — produces a full report with:
    - Executive Summary
    - Financial Ratio Dashboard
    - Competitive Analysis
    - Regulatory Risk Assessment
    - Revenue/Profit Trends
    - SWOT Analysis
    - Investment Recommendation
    - Full citations
    """
    start_time = time.perf_counter()

    query = (
        f"Generate a comprehensive equity research and portfolio report for {request.company_name}"
        f"{f' (ticker: {request.ticker})' if request.ticker else ''}. "
        "Include executive summary, financial ratio analysis (ROE, ROA, D/E ratio, revenue growth, "
        "profit margins), competitive analysis, SWOT analysis, and investment recommendation "
        "(Buy/Hold/Sell with confidence score)."
    )

    if request.include_regulatory_impact:
        query += " Also analyze the impact of recent regulatory changes on this company."
    if request.include_risk_analysis:
        query += " Include a comprehensive risk assessment with risk categories and severity levels."

    conversation = Conversation(
        id=str(uuid7()),
        user_id=user.id,
        title=f"Portfolio Report: {request.company_name}",
        status=ConversationStatus.PROCESSING,
    )
    db.add(conversation)
    await db.flush()

    from app.agents.orchestrator import run_agent_pipeline

    agent_result = await run_agent_pipeline(
        query=query,
        conversation_id=conversation.id,
        user_id=user.id,
        db=db,
        companies=[request.company_name],
        include_regulations=request.include_regulatory_impact,
        include_market_data=True,
        generate_report=True,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    conversation.status = ConversationStatus.COMPLETED

    return ResearchResponse(
        id=conversation.id,
        query=query,
        answer=agent_result.get("answer", ""),
        citations=agent_result.get("citations", []),
        agent_steps=agent_result.get("execution_steps", []),
        report_id=agent_result.get("report_id"),
        latency_ms=latency_ms,
    )
