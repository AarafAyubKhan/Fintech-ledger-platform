"""
FinSight AI — Market Intelligence Agent
Gathers market news, trends, and company announcements.
"""

from datetime import datetime, timezone

import structlog

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

MARKET_INTEL_SYSTEM_PROMPT = """You are the Market Intelligence Agent for FinSight AI.

Your role is to:
1. Analyze market trends relevant to the queried companies
2. Assess competitive landscape
3. Identify major announcements or events
4. Provide market sentiment analysis

Respond with JSON:
{
    "market_overview": "overall market assessment",
    "company_updates": [
        {
            "company": "company name",
            "recent_developments": ["development 1"],
            "market_sentiment": "positive/negative/neutral",
            "competitive_position": "description",
            "key_competitors": ["competitor 1"]
        }
    ],
    "sector_trends": [
        {
            "sector": "sector name",
            "trend": "trend description",
            "impact": "positive/negative/neutral"
        }
    ],
    "risk_factors": ["macro risk 1", "sector risk 2"]
}"""


async def market_intel_node(state: GraphState) -> GraphState:
    """Market Intelligence Agent — gathers market data and competitive analysis."""
    if not state.get("include_market_data", True):
        return {
            **state,
            "current_step": "analysis",
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "market_intel",
                "status": "skipped",
                "message": "Market intelligence not requested",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }

    query = state.get("query", "")
    companies = state.get("companies", [])

    logger.info("market_intel_started", companies=companies)

    # Retrieve market-related documents
    retrieved_docs = []
    try:
        from app.rag.retrieval.hybrid_search import HybridSearchEngine
        search_engine = HybridSearchEngine()

        market_query = f"{query} market trends news {' '.join(companies)}"
        raw_results = await search_engine.search(
            query=market_query,
            top_k=8,
            filters={"document_type": ["news_article", "research_report"]},
        )
        retrieved_docs = [
            {
                "content": r.get("content", ""),
                "source": r.get("document_title", "Unknown"),
                "document_type": r.get("document_type", ""),
            }
            for r in raw_results
        ]
    except Exception as e:
        logger.warning("market_rag_failed", error=str(e))

    llm = get_llm_provider()

    context = "\n---\n".join(
        f"[{doc['source']}]\n{doc['content']}" for doc in retrieved_docs
    ) if retrieved_docs else "No market news documents in knowledge base."

    # Include financial context from previous agents
    fin_research = state.get("analysis_results", {}).get("financial_research", {})
    fin_context = ""
    if fin_research:
        findings = fin_research.get("findings", [])
        if findings:
            fin_context = "\nPrevious Financial Research Findings:\n" + "\n".join(
                f"- {f.get('topic', '')}: {f.get('content', '')[:200]}" for f in findings[:5]
            )

    prompt = f"""Analyze market intelligence for the following query.

Query: {query}
Companies: {', '.join(companies) if companies else 'Not specified'}

Market Documents:
{context}
{fin_context}

Provide market analysis, competitive positioning, and risk factors."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=MARKET_INTEL_SYSTEM_PROMPT,
        )

        market_data = result["content"]
        tokens = result.get("tokens", 0)

        execution_step = {
            "agent_name": "market_intel",
            "status": "completed",
            "message": f"Analyzed market data for {len(market_data.get('company_updates', []))} companies.",
            "data": {
                "companies_analyzed": len(market_data.get("company_updates", [])),
                "sectors_tracked": len(market_data.get("sector_trends", [])),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "market_context": state.get("market_context", []) + retrieved_docs,
            "analysis_results": {
                **state.get("analysis_results", {}),
                "market_intel": market_data,
            },
            "current_step": "analysis",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("market_intel_failed", error=str(e))
        return {
            **state,
            "current_step": "analysis",
            "errors": state.get("errors", []) + [f"Market intel error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "market_intel",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
