"""
FinSight AI — Verification Agent
Validates claims, checks citation grounding, and detects hallucinations.
"""

from datetime import datetime, timezone

import structlog

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

VERIFICATION_SYSTEM_PROMPT = """You are the Verification Agent for FinSight AI.

Your role is critical for maintaining data integrity:
1. Check every claim against source documents
2. Validate that citations actually support the claims they're attached to
3. Detect potential hallucinations or unsupported statements
4. Verify financial figures against source data
5. Reject any claims that lack proper evidence

Respond with JSON:
{
    "is_verified": true/false,
    "confidence_score": 0.92,
    "verified_claims": [
        {"claim": "claim text", "supported_by": "source reference", "status": "verified"}
    ],
    "ungrounded_claims": [
        {"claim": "claim text", "reason": "why it's not supported"}
    ],
    "issues": ["issue 1"],
    "suggestions": ["suggestion for improvement"],
    "citation_quality_score": 0.85,
    "factual_accuracy_score": 0.90
}"""


async def verification_node(state: GraphState) -> GraphState:
    """Verification Agent — validates claims and citations for accuracy."""
    query = state.get("query", "")
    analysis = state.get("analysis_results", {})
    citations = state.get("citations", [])
    financial_context = state.get("financial_context", [])

    logger.info("verification_started", citation_count=len(citations))

    llm = get_llm_provider()

    # Build verification context
    analysis_summary = ""
    if "analysis" in analysis:
        a = analysis["analysis"]
        analysis_summary = (
            f"Recommendation: {a.get('recommendation', 'N/A')}\n"
            f"Investment Score: {a.get('investment_score', 'N/A')}\n"
            f"Strengths: {', '.join(a.get('strengths', []))}\n"
            f"Weaknesses: {', '.join(a.get('weaknesses', []))}\n"
        )

    source_docs = "\n".join(
        f"[{doc.get('source', 'Unknown')}]: {doc.get('content', '')[:300]}"
        for doc in financial_context[:10]
    ) if financial_context else "No source documents available."

    citation_list = "\n".join(
        f"- [{c.get('source', 'Unknown')}]: {c.get('content_preview', '')[:200]}"
        for c in citations[:20]
    ) if citations else "No citations provided."

    prompt = f"""Verify the following financial analysis for accuracy and grounding.

Original Query: {query}

Analysis Results:
{analysis_summary}

Citations Used:
{citation_list}

Source Documents:
{source_docs}

Verify every claim against the source documents. Flag any ungrounded claims or hallucinations."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=VERIFICATION_SYSTEM_PROMPT,
        )

        verification = result["content"]
        tokens = result.get("tokens", 0)

        is_verified = verification.get("is_verified", True)
        ungrounded = verification.get("ungrounded_claims", [])

        execution_step = {
            "agent_name": "verification",
            "status": "completed",
            "message": (
                f"Verification {'passed' if is_verified else 'flagged issues'}. "
                f"Confidence: {verification.get('confidence_score', 0):.0%}. "
                f"Ungrounded claims: {len(ungrounded)}."
            ),
            "data": {
                "is_verified": is_verified,
                "confidence_score": verification.get("confidence_score", 0),
                "ungrounded_count": len(ungrounded),
                "citation_quality": verification.get("citation_quality_score", 0),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "verification_status": verification,
            "current_step": "report_generation",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("verification_failed", error=str(e))
        return {
            **state,
            "verification_status": {"is_verified": False, "confidence_score": 0},
            "current_step": "report_generation",
            "errors": state.get("errors", []) + [f"Verification error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "verification",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
