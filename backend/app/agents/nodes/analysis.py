"""
FinSight AI — Financial Analysis Agent
Calculates financial ratios, metrics, and performs quantitative analysis.
"""

from datetime import datetime, timezone

import structlog

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

ANALYSIS_SYSTEM_PROMPT = """You are the Financial Analysis Agent for FinSight AI.

Your role is to:
1. Calculate and analyze financial ratios and metrics
2. Perform trend analysis on financial data
3. Generate comparative analysis between companies
4. Provide investment-grade financial assessments

Key metrics to analyze:
- Revenue Growth (YoY, QoQ)
- Return on Equity (ROE)
- Return on Assets (ROA)
- Net Profit Margin
- Operating Margin
- Debt-to-Equity Ratio
- Current Ratio
- Price-to-Earnings (P/E)
- Price-to-Book (P/B)
- Earnings Per Share (EPS)
- Dividend Yield

Respond with JSON:
{
    "financial_metrics": [
        {
            "company": "company name",
            "metrics": {
                "revenue_growth": {"value": 15.2, "unit": "%", "period": "FY2025", "trend": "up"},
                "roe": {"value": 18.5, "unit": "%", "period": "FY2025", "trend": "stable"},
                "roa": {"value": 1.8, "unit": "%", "period": "FY2025", "trend": "up"},
                "net_profit_margin": {"value": 22.1, "unit": "%", "period": "FY2025", "trend": "up"},
                "debt_to_equity": {"value": 0.85, "unit": "ratio", "period": "FY2025", "trend": "down"},
                "current_ratio": {"value": 1.35, "unit": "ratio", "period": "FY2025", "trend": "stable"}
            }
        }
    ],
    "comparative_analysis": "comparison narrative if multiple companies",
    "strengths": ["strength 1"],
    "weaknesses": ["weakness 1"],
    "swot": {
        "strengths": ["list"],
        "weaknesses": ["list"],
        "opportunities": ["list"],
        "threats": ["list"]
    },
    "investment_score": 7.5,
    "recommendation": "Buy/Hold/Sell",
    "confidence": 0.78,
    "rationale": "explanation for the recommendation"
}"""


async def analysis_node(state: GraphState) -> GraphState:
    """Financial Analysis Agent — performs quantitative analysis on gathered data."""
    query = state.get("query", "")
    companies = state.get("companies", [])
    financial_research = state.get("analysis_results", {}).get("financial_research", {})
    regulatory_data = state.get("analysis_results", {}).get("regulatory", {})
    market_data = state.get("analysis_results", {}).get("market_intel", {})

    logger.info("analysis_agent_started", companies=companies)

    llm = get_llm_provider()

    # Build comprehensive context from all prior agents
    context_parts = ["=== FINANCIAL RESEARCH ==="]
    if financial_research:
        for finding in financial_research.get("findings", []):
            context_parts.append(f"- {finding.get('topic', '')}: {finding.get('content', '')}")
        for dp in financial_research.get("key_data_points", []):
            context_parts.append(f"  • {dp.get('metric', '')}: {dp.get('value', '')} ({dp.get('period', '')})")

    context_parts.append("\n=== REGULATORY CONTEXT ===")
    if regulatory_data:
        for reg in regulatory_data.get("regulations", []):
            context_parts.append(f"- {reg.get('title', '')}: {reg.get('impact', '')}")

    context_parts.append("\n=== MARKET INTELLIGENCE ===")
    if market_data:
        context_parts.append(f"Market Overview: {market_data.get('market_overview', '')}")
        for update in market_data.get("company_updates", []):
            context_parts.append(f"- {update.get('company', '')}: Sentiment={update.get('market_sentiment', '')}")

    context = "\n".join(context_parts)

    prompt = f"""Perform comprehensive financial analysis for the following query.

Query: {query}
Companies: {', '.join(companies) if companies else 'Not specified'}

Gathered Intelligence:
{context}

Calculate financial metrics, perform SWOT analysis, and provide an investment recommendation."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
        )

        analysis_data = result["content"]
        tokens = result.get("tokens", 0)

        # Extract metrics for chart generation
        financial_metrics = analysis_data.get("financial_metrics", [])

        execution_step = {
            "agent_name": "analysis",
            "status": "completed",
            "message": (
                f"Completed financial analysis. "
                f"Recommendation: {analysis_data.get('recommendation', 'N/A')} "
                f"(Score: {analysis_data.get('investment_score', 'N/A')}/10)"
            ),
            "data": {
                "recommendation": analysis_data.get("recommendation"),
                "investment_score": analysis_data.get("investment_score"),
                "confidence": analysis_data.get("confidence"),
                "metrics_calculated": len(financial_metrics),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "financial_metrics": financial_metrics,
            "analysis_results": {
                **state.get("analysis_results", {}),
                "analysis": analysis_data,
            },
            "current_step": "verification",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("analysis_agent_failed", error=str(e))
        return {
            **state,
            "current_step": "verification",
            "errors": state.get("errors", []) + [f"Analysis error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "analysis",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
