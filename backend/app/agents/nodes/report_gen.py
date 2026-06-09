"""
FinSight AI — Report Generation Agent
Produces structured financial reports with executive summary, analysis, and citations.
"""

from datetime import datetime, timezone

import structlog
from uuid6 import uuid7

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

REPORT_SYSTEM_PROMPT = """You are the Report Generation Agent for FinSight AI.

Generate a professional, investment-grade financial report. The report must be:
1. Well-structured with clear sections
2. Data-driven with specific numbers and percentages
3. Every claim backed by inline citations [Source, Page X]
4. Actionable with clear recommendations
5. Professional tone suitable for institutional investors

Report Structure:
1. Executive Summary (2-3 paragraphs)
2. Key Findings (bullet points)
3. Detailed Analysis (with subsections)
4. Opportunities (specific, actionable)
5. Risks (categorized by severity)
6. Regulatory Impact (if applicable)
7. Recommendation (Buy/Hold/Sell with rationale)

Respond with JSON:
{
    "title": "report title",
    "executive_summary": "multi-paragraph executive summary with citations",
    "key_findings": "bullet-point key findings with citations",
    "detailed_analysis": "comprehensive analysis with subsections and citations",
    "opportunities": "specific opportunities with evidence",
    "risks": "categorized risk assessment",
    "regulatory_impact": "regulatory analysis impact (if applicable)",
    "recommendation": "investment recommendation with rationale and confidence",
    "charts_data": {
        "revenue_trend": [{"period": "FY2023", "value": 100}, {"period": "FY2024", "value": 115}],
        "profit_margin": [{"period": "FY2023", "value": 20.5}, {"period": "FY2024", "value": 22.1}],
        "ratio_comparison": {"roe": 18.5, "roa": 1.8, "de_ratio": 0.85}
    }
}"""


async def report_generation_node(state: GraphState) -> GraphState:
    """Report Generation Agent — creates the final structured report."""
    query = state.get("query", "")
    companies = state.get("companies", [])
    analysis = state.get("analysis_results", {})
    citations = state.get("citations", [])
    verification = state.get("verification_status", {})
    metrics = state.get("financial_metrics", [])

    logger.info("report_generation_started", companies=companies)

    llm = get_llm_provider()

    # Build comprehensive context
    context_parts = []

    # Financial research findings
    fin_research = analysis.get("financial_research", {})
    if fin_research:
        context_parts.append("=== FINANCIAL RESEARCH ===")
        for f in fin_research.get("findings", []):
            context_parts.append(f"• {f.get('topic', '')}: {f.get('content', '')}")

    # Regulatory analysis
    reg_data = analysis.get("regulatory", {})
    if reg_data and reg_data.get("regulations"):
        context_parts.append("\n=== REGULATORY ANALYSIS ===")
        context_parts.append(reg_data.get("overall_regulatory_impact", ""))

    # Market intelligence
    market = analysis.get("market_intel", {})
    if market:
        context_parts.append("\n=== MARKET INTELLIGENCE ===")
        context_parts.append(market.get("market_overview", ""))

    # Financial analysis
    fin_analysis = analysis.get("analysis", {})
    if fin_analysis:
        context_parts.append("\n=== FINANCIAL ANALYSIS ===")
        context_parts.append(f"Recommendation: {fin_analysis.get('recommendation', 'N/A')}")
        context_parts.append(f"Investment Score: {fin_analysis.get('investment_score', 'N/A')}/10")
        if fin_analysis.get("swot"):
            swot = fin_analysis["swot"]
            context_parts.append(f"Strengths: {', '.join(swot.get('strengths', []))}")
            context_parts.append(f"Weaknesses: {', '.join(swot.get('weaknesses', []))}")
            context_parts.append(f"Opportunities: {', '.join(swot.get('opportunities', []))}")
            context_parts.append(f"Threats: {', '.join(swot.get('threats', []))}")

    # Verification status
    if verification:
        context_parts.append(f"\n=== VERIFICATION ===")
        context_parts.append(f"Verified: {verification.get('is_verified', False)}")
        context_parts.append(f"Confidence: {verification.get('confidence_score', 0):.0%}")

    # Citations
    context_parts.append(f"\n=== AVAILABLE CITATIONS ({len(citations)}) ===")
    for c in citations[:15]:
        context_parts.append(f"- [{c.get('source', '')}] {c.get('content_preview', '')[:150]}")

    context = "\n".join(context_parts)

    prompt = f"""Generate a comprehensive financial research report.

Query: {query}
Companies: {', '.join(companies) if companies else 'Not specified'}

All Gathered Intelligence:
{context}

Generate a professional investment-grade report with all sections. Include inline citations."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=REPORT_SYSTEM_PROMPT,
            temperature=0.3,
        )

        report_data = result["content"]
        tokens = result.get("tokens", 0)

        # Construct the full answer text
        answer_parts = []
        if report_data.get("executive_summary"):
            answer_parts.append(f"## Executive Summary\n{report_data['executive_summary']}")
        if report_data.get("key_findings"):
            answer_parts.append(f"\n## Key Findings\n{report_data['key_findings']}")
        if report_data.get("detailed_analysis"):
            answer_parts.append(f"\n## Detailed Analysis\n{report_data['detailed_analysis']}")
        if report_data.get("opportunities"):
            answer_parts.append(f"\n## Opportunities\n{report_data['opportunities']}")
        if report_data.get("risks"):
            answer_parts.append(f"\n## Risks\n{report_data['risks']}")
        if report_data.get("regulatory_impact"):
            answer_parts.append(f"\n## Regulatory Impact\n{report_data['regulatory_impact']}")
        if report_data.get("recommendation"):
            answer_parts.append(f"\n## Recommendation\n{report_data['recommendation']}")

        answer = "\n".join(answer_parts)

        execution_step = {
            "agent_name": "report_generation",
            "status": "completed",
            "message": f"Generated report: {report_data.get('title', 'Financial Analysis Report')}",
            "data": {
                "title": report_data.get("title"),
                "word_count": len(answer.split()),
                "has_charts": bool(report_data.get("charts_data")),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "answer": answer,
            "report": report_data,
            "current_step": "complete",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("report_generation_failed", error=str(e))
        # Fallback: create a basic answer from available data
        fallback_answer = f"Analysis for: {query}\n\n"
        if fin_analysis:
            fallback_answer += f"Recommendation: {fin_analysis.get('recommendation', 'N/A')}\n"
        fallback_answer += "\nNote: Full report generation encountered an error."

        return {
            **state,
            "answer": fallback_answer,
            "current_step": "complete",
            "errors": state.get("errors", []) + [f"Report generation error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "report_generation",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
