"""
FinSight AI — Regulatory Agent
Searches regulatory knowledge base for RBI/SEBI circulars and banking regulations.
"""

import json
from datetime import datetime, timezone

import structlog

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

REGULATORY_SYSTEM_PROMPT = """You are the Regulatory Agent for FinSight AI.

Your role is to:
1. Analyze regulatory documents (RBI circulars, SEBI notifications, banking regulations)
2. Assess the impact of regulations on specific companies or sectors
3. Identify compliance requirements and risks
4. Provide regulatory citations

Always cite the specific regulation with its reference number and date.

Respond with JSON:
{
    "regulations": [
        {
            "title": "regulation title",
            "issuer": "RBI/SEBI",
            "reference": "circular number",
            "date": "date",
            "summary": "brief summary",
            "impact": "impact on the queried companies",
            "affected_sectors": ["banking", "insurance"],
            "compliance_requirements": ["requirement 1"],
            "risk_level": "high/medium/low"
        }
    ],
    "overall_regulatory_impact": "summary of combined regulatory impact",
    "key_risks": ["risk 1", "risk 2"]
}"""


async def regulatory_node(state: GraphState) -> GraphState:
    """Regulatory Agent — analyzes regulatory impact on queried companies."""
    if not state.get("include_regulations", True):
        return {
            **state,
            "current_step": "market_intel",
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "regulatory",
                "status": "skipped",
                "message": "Regulatory analysis not requested",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }

    query = state.get("query", "")
    companies = state.get("companies", [])

    logger.info("regulatory_agent_started", companies=companies)

    # Retrieve regulatory documents
    retrieved_docs = []
    try:
        from app.rag.retrieval.hybrid_search import HybridSearchEngine
        search_engine = HybridSearchEngine()

        reg_query = f"{query} RBI SEBI regulation circular banking {' '.join(companies)}"
        raw_results = await search_engine.search(
            query=reg_query,
            top_k=8,
            filters={"document_type": ["regulatory_circular"]},
        )
        retrieved_docs = [
            {
                "content": r.get("content", ""),
                "source": r.get("document_title", "Unknown"),
                "page_number": r.get("page_number"),
                "document_id": r.get("document_id", ""),
                "chunk_id": r.get("chunk_id", ""),
            }
            for r in raw_results
        ]
    except Exception as e:
        logger.warning("regulatory_rag_failed", error=str(e))

    llm = get_llm_provider()

    context = "\n---\n".join(
        f"[{doc['source']}]\n{doc['content']}" for doc in retrieved_docs
    ) if retrieved_docs else "No regulatory documents found in knowledge base."

    prompt = f"""Analyze regulatory impact for the following query.

Query: {query}
Companies: {', '.join(companies) if companies else 'Not specified'}

Retrieved Regulatory Documents:
{context}

Identify relevant regulations and their impact."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=REGULATORY_SYSTEM_PROMPT,
        )

        reg_data = result["content"]
        tokens = result.get("tokens", 0)

        # Build citations
        citations = []
        for reg in reg_data.get("regulations", []):
            citations.append({
                "source": f"{reg.get('issuer', '')} - {reg.get('title', '')}",
                "page": None,
                "content_preview": reg.get("summary", "")[:200],
            })

        execution_step = {
            "agent_name": "regulatory",
            "status": "completed",
            "message": f"Found {len(reg_data.get('regulations', []))} relevant regulations.",
            "data": {"regulation_count": len(reg_data.get("regulations", []))},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "regulatory_context": state.get("regulatory_context", []) + retrieved_docs,
            "citations": state.get("citations", []) + citations,
            "analysis_results": {
                **state.get("analysis_results", {}),
                "regulatory": reg_data,
            },
            "current_step": "market_intel",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("regulatory_agent_failed", error=str(e))
        return {
            **state,
            "current_step": "market_intel",
            "errors": state.get("errors", []) + [f"Regulatory error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "regulatory",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
