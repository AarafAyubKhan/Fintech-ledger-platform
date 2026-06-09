"""
FinSight AI — Graph-Aware Retrieval
Augments vector retrieval with knowledge graph traversal for
richer, multi-hop context.
"""

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.knowledge_graph.graph_store import KGEntity, KnowledgeGraphStore

logger = structlog.get_logger()


class GraphRetriever:
    """Combines knowledge graph traversal with vector search results."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.store = KnowledgeGraphStore(db)

    async def retrieve_with_graph(
        self,
        query: str,
        vector_results: list[dict[str, Any]],
        max_graph_hops: int = 1,
        max_graph_entities: int = 10,
    ) -> dict[str, Any]:
        """Augment vector search results with graph context.
        
        1. Extract entity mentions from query + vector results
        2. Traverse the knowledge graph for connected entities
        3. Return merged context with graph relationships
        
        Args:
            query: User's original query.
            vector_results: Results from vector search.
            max_graph_hops: Maximum graph traversal depth.
            max_graph_entities: Max entities to include.
        
        Returns:
            Dict with vector_results, graph_entities, graph_relationships,
            and enriched_context.
        """
        # Step 1: Extract entity names from query and results
        entity_names = self._extract_entity_mentions(query, vector_results)

        if not entity_names:
            return {
                "vector_results": vector_results,
                "graph_entities": [],
                "graph_relationships": [],
                "enriched_context": [],
            }

        # Step 2: Find matching entities in the graph
        matched_entities: list[KGEntity] = []
        for name in entity_names[:max_graph_entities]:
            entities = await self.store.search_entities(query=name, limit=3)
            matched_entities.extend(entities)

        # Deduplicate
        seen_ids = set()
        unique_entities = []
        for e in matched_entities:
            if e.id not in seen_ids:
                seen_ids.add(e.id)
                unique_entities.append(e)

        # Step 3: Traverse neighbors
        all_relationships = []
        neighbor_entities = []

        for entity in unique_entities[:max_graph_entities]:
            graph_data = await self.store.get_entity_neighbors(
                entity.id, max_depth=max_graph_hops
            )
            neighbor_entities.extend(graph_data["neighbors"])
            all_relationships.extend(graph_data["relationships"])

        # Deduplicate neighbors
        for n in neighbor_entities:
            if n.id not in seen_ids:
                seen_ids.add(n.id)
                unique_entities.append(n)

        # Step 4: Build enriched context
        enriched_context = self._build_enriched_context(
            unique_entities, all_relationships
        )

        logger.info(
            "graph_retrieval_complete",
            query_entities=len(entity_names),
            matched=len(unique_entities),
            relationships=len(all_relationships),
        )

        return {
            "vector_results": vector_results,
            "graph_entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "properties": e.properties,
                }
                for e in unique_entities
            ],
            "graph_relationships": [
                {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.relationship_type,
                    "properties": r.properties,
                }
                for r in all_relationships
            ],
            "enriched_context": enriched_context,
        }

    def _extract_entity_mentions(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[str]:
        """Extract potential entity names from query and search results.
        
        Uses simple heuristics (capitalized words, known patterns).
        In production, this would use NER.
        """
        mentions = set()

        # Extract capitalized multi-word names from query
        words = query.split()
        i = 0
        while i < len(words):
            if words[i][0:1].isupper():
                # Collect consecutive capitalized words
                name_parts = [words[i]]
                j = i + 1
                while j < len(words) and words[j][0:1].isupper():
                    name_parts.append(words[j])
                    j += 1
                name = " ".join(name_parts)
                if len(name) > 2:
                    mentions.add(name)
                i = j
            else:
                i += 1

        # Extract from result metadata
        for result in results:
            payload = result.get("payload", {})
            doc_title = payload.get("document_title", "")
            if doc_title:
                mentions.add(doc_title)
            company_id = payload.get("company_id")
            if company_id:
                mentions.add(company_id)

        return list(mentions)

    def _build_enriched_context(
        self,
        entities: list[KGEntity],
        relationships: list,
    ) -> list[str]:
        """Build natural language context strings from graph data."""
        context_lines = []

        # Entity descriptions
        for entity in entities:
            props = entity.properties or {}
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items()) if props else ""
            line = f"[{entity.entity_type}] {entity.name}"
            if prop_str:
                line += f" ({prop_str})"
            context_lines.append(line)

        # Relationship descriptions
        entity_map = {e.id: e.name for e in entities}
        for rel in relationships:
            source = entity_map.get(rel.source_id, rel.source_id)
            target = entity_map.get(rel.target_id, rel.target_id)
            context_lines.append(
                f"  → {source} --[{rel.relationship_type}]--> {target}"
            )

        return context_lines
