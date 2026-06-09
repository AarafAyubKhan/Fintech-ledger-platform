"""
FinSight AI — LangGraph Orchestrator
Multi-agent workflow graph that coordinates all specialized agents.

Flow:
    Planner → Financial Research → Regulatory → Market Intel → Analysis → Verification → Report Gen
"""

from datetime import datetime, timezone
from typing import Any

import structlog
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.agents.state import GraphState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.financial_research import financial_research_node
from app.agents.nodes.regulatory import regulatory_node
from app.agents.nodes.market_intel import market_intel_node
from app.agents.nodes.analysis import analysis_node
from app.agents.nodes.verification import verification_node
from app.agents.nodes.report_gen import report_generation_node

logger = structlog.get_logger()


def should_continue_to_report(state: GraphState) -> str:
    """Conditional edge: determine if we should generate a report or return directly."""
    if state.get("generate_report", False):
        return "report_generation"
    return "report_generation"  # Always generate a report for now


def check_verification(state: GraphState) -> str:
    """Conditional edge after verification: retry research or proceed to report."""
    verification = state.get("verification_status", {})
    confidence = verification.get("confidence_score", 1.0)
    ungrounded = verification.get("ungrounded_claims", [])

    # If too many ungrounded claims, the report still proceeds but with caveats
    if confidence < 0.3 and len(ungrounded) > 5:
        logger.warning("low_verification_confidence", confidence=confidence)

    return "report_generation"


def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph workflow connecting all agents.

    Graph:
        planner → financial_research → regulatory → market_intel
        → analysis → verification → report_generation → END
    """
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("financial_research", financial_research_node)
    workflow.add_node("regulatory", regulatory_node)
    workflow.add_node("market_intel", market_intel_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("report_generation", report_generation_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Add edges (sequential pipeline)
    workflow.add_edge("planner", "financial_research")
    workflow.add_edge("financial_research", "regulatory")
    workflow.add_edge("regulatory", "market_intel")
    workflow.add_edge("market_intel", "analysis")
    workflow.add_edge("analysis", "verification")

    # Conditional edge after verification
    workflow.add_conditional_edges(
        "verification",
        check_verification,
        {
            "report_generation": "report_generation",
        },
    )

    # End after report generation
    workflow.add_edge("report_generation", END)

    return workflow


# Compile the graph once at module level
agent_graph = build_agent_graph().compile()


async def run_agent_pipeline(
    query: str,
    conversation_id: str,
    user_id: str,
    db: AsyncSession,
    companies: list[str] | None = None,
    include_regulations: bool = True,
    include_market_data: bool = True,
    generate_report: bool = False,
) -> dict[str, Any]:
    """
    Execute the full multi-agent pipeline for a user query.
    
    Returns a dict with:
        - answer: The final generated response
        - citations: List of citation objects
        - execution_steps: Trace of all agent executions
        - report_id: ID of the saved report (if generated)
        - total_tokens: Total tokens consumed
        - state_snapshot: Serialized final state
    """
    logger.info(
        "pipeline_started",
        query=query[:100],
        conversation_id=conversation_id,
        companies=companies,
    )

    # Initialize state
    initial_state: GraphState = {
        "query": query,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "companies": companies or [],
        "include_regulations": include_regulations,
        "include_market_data": include_market_data,
        "generate_report": generate_report,
        "plan": [],
        "subtasks": [],
        "financial_context": [],
        "regulatory_context": [],
        "market_context": [],
        "analysis_results": {},
        "financial_metrics": [],
        "verification_status": {},
        "citations": [],
        "answer": "",
        "report": {},
        "report_id": "",
        "current_step": "planner",
        "execution_steps": [],
        "errors": [],
        "total_tokens": 0,
    }

    try:
        # Execute the graph
        final_state = await agent_graph.ainvoke(initial_state)

        # Save report to database if generated
        report_id = None
        if final_state.get("report"):
            report_id = await _save_report(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
                report_data=final_state["report"],
                citations=final_state.get("citations", []),
                metrics=final_state.get("financial_metrics", []),
                companies=final_state.get("companies", []),
            )

        logger.info(
            "pipeline_completed",
            conversation_id=conversation_id,
            total_tokens=final_state.get("total_tokens", 0),
            steps=len(final_state.get("execution_steps", [])),
            errors=len(final_state.get("errors", [])),
        )

        return {
            "answer": final_state.get("answer", ""),
            "citations": final_state.get("citations", []),
            "execution_steps": final_state.get("execution_steps", []),
            "report_id": report_id,
            "total_tokens": final_state.get("total_tokens", 0),
            "final_agent": "report_generation",
            "sources": _extract_sources(final_state),
            "state_snapshot": {
                "companies": final_state.get("companies", []),
                "current_step": final_state.get("current_step", ""),
                "error_count": len(final_state.get("errors", [])),
            },
        }

    except Exception as e:
        logger.exception("pipeline_error", error=str(e))
        return {
            "answer": f"I encountered an error while processing your request: {str(e)}",
            "citations": [],
            "execution_steps": initial_state.get("execution_steps", []),
            "report_id": None,
            "total_tokens": initial_state.get("total_tokens", 0),
            "final_agent": "error",
            "sources": [],
            "state_snapshot": {},
        }


async def _save_report(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
    report_data: dict,
    citations: list,
    metrics: list,
    companies: list,
) -> str:
    """Persist a generated report to the database."""
    from app.models.report import Report, ReportType

    report_id = str(uuid7())

    # Determine report type
    report_type = ReportType.CUSTOM
    title = report_data.get("title", "Financial Analysis Report")
    if "portfolio" in title.lower() or "equity" in title.lower():
        report_type = ReportType.PORTFOLIO_REPORT
    elif "compar" in title.lower():
        report_type = ReportType.COMPARATIVE_ANALYSIS

    content = report_data.get("detailed_analysis", "")
    answer_text = ""
    for key in ["executive_summary", "key_findings", "detailed_analysis",
                 "opportunities", "risks", "regulatory_impact", "recommendation"]:
        if report_data.get(key):
            answer_text += f"\n\n## {key.replace('_', ' ').title()}\n{report_data[key]}"

    report = Report(
        id=report_id,
        user_id=user_id,
        conversation_id=conversation_id,
        title=title,
        report_type=report_type,
        executive_summary=report_data.get("executive_summary"),
        key_findings=report_data.get("key_findings"),
        detailed_analysis=report_data.get("detailed_analysis"),
        opportunities=report_data.get("opportunities"),
        risks=report_data.get("risks"),
        regulatory_impact=report_data.get("regulatory_impact"),
        recommendation=report_data.get("recommendation"),
        full_content=answer_text,
        companies=companies,
        citations=citations,
        financial_metrics=metrics[0] if metrics else None,
        charts_data=report_data.get("charts_data"),
        word_count=len(answer_text.split()),
        source_count=len(citations),
    )
    db.add(report)
    await db.flush()

    logger.info("report_saved", report_id=report_id, title=title)
    return report_id


def _extract_sources(state: GraphState) -> list[dict]:
    """Extract unique source documents from all contexts."""
    sources = {}
    for ctx_key in ["financial_context", "regulatory_context", "market_context"]:
        for doc in state.get(ctx_key, []):
            source_name = doc.get("source", "Unknown")
            if source_name not in sources:
                sources[source_name] = {
                    "source": source_name,
                    "document_id": doc.get("document_id", ""),
                    "document_type": doc.get("document_type", ""),
                    "page_number": doc.get("page_number"),
                }
    return list(sources.values())
