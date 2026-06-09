"""
FinSight AI — Financial Research Agent
RAG-powered retrieval of financial documents, annual reports, and earnings data.
"""

import json
from datetime import datetime, timezone

import structlog

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

RESEARCH_SYSTEM_PROMPT = """You are the Financial Research Agent for FinSight AI.

Your role is to:
1. Search the knowledge base for relevant financial documents
2. Retrieve annual reports, quarterly reports, earnings transcripts, and financial statements
3. Extract key financial data and insights from retrieved documents
4. Provide source citations for every piece of information

CRITICAL RULES:
- Every claim must be backed by a source citation in format [Source Title, Page X]
- Never fabricate data — only use information from retrieved documents
- If insufficient data is available, clearly state the limitations
- Include specific numbers, percentages, and dates where available

Respond with a JSON object:
{
    "findings": [
        {
            "topic": "topic name",
            "content": "detailed finding with inline citations",
            "sources": [{"source": "document name", "page": 42, "chunk_id": "id"}],
            "confidence": 0.95
        }
    ],
    "key_data_points": [
        {"metric": "Revenue", "value": "50000 Cr", "period": "FY2025", "source": "Annual Report 2025"}
    ],
    "gaps": ["list of data points that could not be found"]
}"""


async def financial_research_node(state: GraphState) -> GraphState:
    """
    Financial Research Agent — retrieves and synthesizes financial data using RAG.
    """
    query = state.get("query", "")
    companies = state.get("companies", [])

    logger.info("financial_research_started", companies=companies)

    # Retrieve relevant documents from Qdrant
    retrieved_docs = []
    try:
        from app.rag.retrieval.hybrid_search import HybridSearchEngine
        search_engine = HybridSearchEngine()

        search_query = f"{query} {' '.join(companies)} financial data annual report"
        raw_results = await search_engine.search(
            query=search_query,
            top_k=10,
            filters={"companies": companies} if companies else None,
        )

        retrieved_docs = [
            {
                "content": r.get("content", ""),
                "source": r.get("document_title", "Unknown"),
                "page_number": r.get("page_number"),
                "document_id": r.get("document_id", ""),
                "chunk_id": r.get("chunk_id", ""),
                "document_type": r.get("document_type", ""),
                "relevance_score": r.get("score", 0.0),
            }
            for r in raw_results
        ]
    except Exception as e:
        logger.warning("rag_retrieval_failed", error=str(e))

    llm = get_llm_provider()

    # Build context from retrieved documents
    context_parts = []
    for i, doc in enumerate(retrieved_docs):
        context_parts.append(
            f"[Document {i+1}: {doc['source']}, Page {doc.get('page_number', 'N/A')}]\n"
            f"{doc['content']}\n"
        )
    context = "\n---\n".join(context_parts) if context_parts else "No documents retrieved from the knowledge base."

    prompt = f"""Research the following financial query using the retrieved documents.

Query: {query}
Companies of Interest: {', '.join(companies) if companies else 'Not specified'}

Retrieved Documents:
{context}

Analyze the documents and extract relevant financial information. Cite every claim."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
        )

        research_data = result["content"]
        tokens = result.get("tokens", 0)

        # Build citations from findings
        citations = []
        findings = research_data.get("findings", [])
        for finding in findings:
            for source in finding.get("sources", []):
                citations.append({
                    "source": source.get("source", ""),
                    "page": source.get("page"),
                    "chunk_id": source.get("chunk_id", ""),
                    "content_preview": finding.get("content", "")[:200],
                })

        execution_step = {
            "agent_name": "financial_research",
            "status": "completed",
            "message": f"Retrieved {len(retrieved_docs)} documents, extracted {len(findings)} findings.",
            "data": {
                "documents_retrieved": len(retrieved_docs),
                "findings_count": len(findings),
                "gaps": research_data.get("gaps", []),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "financial_context": state.get("financial_context", []) + retrieved_docs,
            "citations": state.get("citations", []) + citations,
            "analysis_results": {
                **state.get("analysis_results", {}),
                "financial_research": research_data,
            },
            "current_step": "regulatory",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("financial_research_failed", error=str(e))
        return {
            **state,
            "current_step": "regulatory",
            "errors": state.get("errors", []) + [f"Financial research error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "financial_research",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
