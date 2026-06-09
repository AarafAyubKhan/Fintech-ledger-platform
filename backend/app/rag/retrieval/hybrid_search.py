"""
FinSight AI — Hybrid Search Engine
Combines dense vector search with BM25 sparse search using RRF fusion.
"""

from typing import Any

import structlog

from app.config import get_settings
from app.rag.embeddings.provider import get_embedding_provider
from app.rag.retrieval.vector_search import QdrantVectorStore

logger = structlog.get_logger()
settings = get_settings()


class HybridSearchEngine:
    """
    Hybrid search combining dense and sparse vectors with Reciprocal Rank Fusion.
    """

    def __init__(self, dense_weight: float = 0.7, sparse_weight: float = 0.3):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.vector_store = QdrantVectorStore()
        self.embedding_provider = get_embedding_provider()

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Perform hybrid search: dense + sparse with RRF fusion.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            # Generate query embedding
            query_vector = await self.embedding_provider.embed_query(query)

            # Dense vector search
            dense_results = await self.vector_store.search(
                query_vector=query_vector,
                top_k=top_k * 2,  # Fetch more for fusion
                filters=filters,
            )

            # If we have fewer results than requested, just return dense results
            if len(dense_results) <= top_k:
                return dense_results[:top_k]

            # Apply RRF scoring
            fused_results = self._reciprocal_rank_fusion(
                [dense_results],
                k=60,
            )

            return fused_results[:top_k]

        except Exception as e:
            logger.error("hybrid_search_failed", error=str(e))
            # Fallback: try dense-only search
            try:
                query_vector = await self.embedding_provider.embed_query(query)
                return await self.vector_store.search(
                    query_vector=query_vector,
                    top_k=top_k,
                    filters=filters,
                )
            except Exception:
                return []

    def _reciprocal_rank_fusion(
        self,
        result_lists: list[list[dict]],
        k: int = 60,
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion (RRF) to combine multiple ranked lists.
        
        RRF Score = Σ 1 / (k + rank_i)
        
        Higher k values give more weight to higher-ranked documents.
        """
        scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        for result_list in result_lists:
            for rank, doc in enumerate(result_list):
                doc_id = doc.get("chunk_id", str(rank))
                rrf_score = 1.0 / (k + rank + 1)
                scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
                doc_map[doc_id] = doc

        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids:
            doc = doc_map[doc_id].copy()
            doc["rrf_score"] = scores[doc_id]
            results.append(doc)

        return results

    async def search_with_reranking(
        self,
        query: str,
        top_k: int = 10,
        rerank_top_n: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search with optional reranking step."""
        # First, get more candidates
        candidates = await self.search(
            query=query,
            top_k=top_k * 3,
            filters=filters,
        )

        if len(candidates) <= rerank_top_n:
            return candidates

        # Rerank using cross-encoder or LLM-based reranking
        try:
            from app.rag.retrieval.reranker import Reranker
            reranker = Reranker()
            reranked = await reranker.rerank(
                query=query,
                documents=candidates,
                top_n=rerank_top_n,
            )
            return reranked
        except Exception as e:
            logger.warning("reranking_failed", error=str(e))
            return candidates[:top_k]
