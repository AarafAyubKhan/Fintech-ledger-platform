"""
FinSight AI — Knowledge Graph Extractor
Uses LLM to extract entities (Company, Regulation, Metric, Industry)
and relationships from document content.
"""

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.agents.llm.provider import get_llm_provider

logger = structlog.get_logger()

EXTRACTION_PROMPT = """You are a financial knowledge graph extraction agent.

Given the following document text, extract all entities and relationships.

Entity types:
- COMPANY: Company names (e.g., HDFC Bank, ICICI Bank, Reliance Industries)
- REGULATION: Regulatory bodies and their circulars (e.g., RBI, SEBI, Basel III norms)
- METRIC: Financial metrics (e.g., ROE, Net Interest Margin, Revenue, EPS)
- INDUSTRY: Industry sectors (e.g., Banking, IT, Pharma, Oil & Gas)
- PERSON: Key executives and officials
- EVENT: Financial events (e.g., Merger, IPO, Quarterly Results)

Relationship types:
- BELONGS_TO: Company belongs to Industry
- REGULATED_BY: Company/Industry regulated by Regulation
- HAS_METRIC: Company has Metric with a value
- COMPETES_WITH: Company competes with Company
- SUBSIDIARY_OF: Company is subsidiary of Company
- MENTIONED_IN: Entity mentioned in document
- IMPACTS: Event/Regulation impacts Company/Industry

Respond with a JSON object:
{
    "entities": [
        {"name": "entity name", "type": "ENTITY_TYPE", "properties": {"key": "value"}}
    ],
    "relationships": [
        {"source": "entity name", "target": "entity name", "type": "RELATIONSHIP_TYPE", "properties": {"key": "value"}}
    ]
}"""


class KnowledgeGraphExtractor:
    """Extracts entities and relationships from document content."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def extract_from_document(
        self,
        content: str,
        document_id: str,
        document_title: str,
        max_content_length: int = 8000,
    ) -> dict[str, Any]:
        """Extract knowledge graph entities and relationships from text.
        
        Args:
            content: Raw document text.
            document_id: Source document ID for provenance.
            document_title: Source document title.
            max_content_length: Max chars to send to LLM.
        
        Returns:
            Dict with extracted entities and relationships.
        """
        # Truncate content for LLM context window
        truncated = content[:max_content_length]

        llm = get_llm_provider()

        prompt = f"""Extract entities and relationships from this financial document.

Document Title: {document_title}
Document Text:
---
{truncated}
---

Extract all financial entities and their relationships."""

        try:
            result = await llm.generate_structured(
                prompt=prompt,
                system_prompt=EXTRACTION_PROMPT,
            )

            kg_data = result.get("content", {})
            entities = kg_data.get("entities", [])
            relationships = kg_data.get("relationships", [])

            # Store in graph
            from app.rag.knowledge_graph.graph_store import KnowledgeGraphStore
            store = KnowledgeGraphStore(self.db)

            stored_entities = []
            for entity in entities:
                entity_id = await store.upsert_entity(
                    name=entity.get("name", ""),
                    entity_type=entity.get("type", "UNKNOWN"),
                    properties=entity.get("properties", {}),
                    source_document_id=document_id,
                )
                stored_entities.append(entity_id)

            stored_rels = []
            for rel in relationships:
                rel_id = await store.upsert_relationship(
                    source_name=rel.get("source", ""),
                    target_name=rel.get("target", ""),
                    relationship_type=rel.get("type", "RELATED_TO"),
                    properties=rel.get("properties", {}),
                    source_document_id=document_id,
                )
                if rel_id:
                    stored_rels.append(rel_id)

            logger.info(
                "kg_extraction_complete",
                doc_id=document_id,
                entities=len(stored_entities),
                relationships=len(stored_rels),
            )

            return {
                "entities": len(stored_entities),
                "relationships": len(stored_rels),
                "raw_entities": entities,
                "raw_relationships": relationships,
            }

        except Exception as e:
            logger.error("kg_extraction_failed", doc_id=document_id, error=str(e))
            raise
