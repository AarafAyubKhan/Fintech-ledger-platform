"""
FinSight AI — Reranker
BGE-style reranking layer for improving search result quality.
"""

import structlog

from app.agents.llm.provider import get_llm_provider

logger = structlog.get_logger()


class Reranker:
    """
    Reranker that uses LLM-based relevance scoring.
    Architecture allows easy replacement with dedicated models (BGE, Cohere, etc.)
    """

    async def rerank(
        self,
        query: str,
        documents: list[dict],
        top_n: int = 5,
    ) -> list[dict]:
        """
        Rerank documents by relevance to the query.
        Uses LLM as a cross-encoder for reranking.
        """
        if len(documents) <= top_n:
            return documents

        llm = get_llm_provider()

        # Build document list for scoring
        doc_list = "\n".join(
            f"Document {i+1}: {doc.get('content', '')[:300]}"
            for i, doc in enumerate(documents[:20])  # Limit to top 20 candidates
        )

        prompt = f"""Score the relevance of each document to the query on a scale of 0-10.

Query: {query}

Documents:
{doc_list}

Respond with JSON:
{{"scores": [
    {{"doc_index": 1, "score": 8.5, "reason": "highly relevant"}},
    ...
]}}"""

        try:
            result = await llm.generate_structured(prompt=prompt)
            scores = result["content"].get("scores", [])

            # Map scores to documents
            score_map = {s.get("doc_index", i + 1): s.get("score", 0) for i, s in enumerate(scores)}

            scored_docs = []
            for i, doc in enumerate(documents[:20]):
                doc_copy = doc.copy()
                doc_copy["rerank_score"] = score_map.get(i + 1, 0)
                scored_docs.append(doc_copy)

            # Sort by rerank score
            scored_docs.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return scored_docs[:top_n]

        except Exception as e:
            logger.warning("reranking_error", error=str(e))
            return documents[:top_n]
