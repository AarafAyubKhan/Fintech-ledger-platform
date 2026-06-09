"""
FinSight AI — Qdrant Vector Store
Dense vector search using Qdrant.
"""

from typing import Any

import structlog
from qdrant_client import QdrantClient, models

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class QdrantVectorStore:
    """Manages Qdrant vector storage and retrieval."""

    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key or None,
        )
        self.collection_name = settings.qdrant_collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense": models.VectorParams(
                            size=settings.embedding_dimension,
                            distance=models.Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        "sparse": models.SparseVectorParams()
                    },
                )
                logger.info("qdrant_collection_created", name=self.collection_name)
            else:
                logger.info("qdrant_collection_exists", name=self.collection_name)
        except Exception as e:
            logger.warning("qdrant_collection_check_failed", error=str(e))

    async def upsert_points(self, points: list[dict]) -> None:
        """Upsert embedding points into Qdrant."""
        try:
            qdrant_points = [
                models.PointStruct(
                    id=p["id"],
                    vector={"dense": p["vector"]},
                    payload=p.get("payload", {}),
                )
                for p in points
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points,
            )
            logger.info("points_upserted", count=len(points))
        except Exception as e:
            logger.error("upsert_failed", error=str(e))
            raise

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Perform dense vector search."""
        try:
            search_filter = self._build_filter(filters) if filters else None

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="dense", vector=query_vector),
                limit=top_k,
                query_filter=search_filter,
                with_payload=True,
            )

            return [
                {
                    "chunk_id": str(r.id),
                    "score": r.score,
                    **r.payload,
                }
                for r in results
            ]
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []

    def _build_filter(self, filters: dict) -> models.Filter:
        """Build a Qdrant filter from a dict."""
        conditions = []

        if "companies" in filters and filters["companies"]:
            conditions.append(
                models.FieldCondition(
                    key="company_id",
                    match=models.MatchAny(any=filters["companies"]),
                )
            )

        if "document_type" in filters and filters["document_type"]:
            doc_types = filters["document_type"]
            if isinstance(doc_types, str):
                doc_types = [doc_types]
            conditions.append(
                models.FieldCondition(
                    key="document_type",
                    match=models.MatchAny(any=doc_types),
                )
            )

        return models.Filter(must=conditions) if conditions else models.Filter()

    async def delete_by_document(self, document_id: str) -> None:
        """Delete all points for a specific document."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )
            logger.info("points_deleted", document_id=document_id)
        except Exception as e:
            logger.error("delete_failed", error=str(e))
