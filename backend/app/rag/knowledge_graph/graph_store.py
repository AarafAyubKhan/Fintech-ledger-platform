"""
FinSight AI — Knowledge Graph Store
PostgreSQL-backed graph storage using JSON adjacency model.
Stores entities and edges with provenance tracking.
"""

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import Column, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid6 import uuid7

from app.core.database import Base

logger = structlog.get_logger()


class KGEntity(Base):
    """A node in the knowledge graph."""
    __tablename__ = "kg_entities"

    id = Column(String(36), primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    properties = Column(JSONB, default={})
    source_documents = Column(JSONB, default=[])  # list of document IDs
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_kg_entities_name_type", "name", "entity_type", unique=True),
    )


class KGRelationship(Base):
    """An edge in the knowledge graph."""
    __tablename__ = "kg_relationships"

    id = Column(String(36), primary_key=True)
    source_id = Column(String(36), nullable=False, index=True)
    target_id = Column(String(36), nullable=False, index=True)
    relationship_type = Column(String(100), nullable=False, index=True)
    properties = Column(JSONB, default={})
    source_documents = Column(JSONB, default=[])
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_kg_rels_source_target_type",
            "source_id",
            "target_id",
            "relationship_type",
            unique=True,
        ),
    )


class KnowledgeGraphStore:
    """CRUD operations for the knowledge graph stored in PostgreSQL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_entity(
        self,
        name: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
        source_document_id: str | None = None,
    ) -> str:
        """Create or update an entity. Returns entity ID."""
        if not name.strip():
            return ""

        # Check if entity already exists
        result = await self.db.execute(
            select(KGEntity).where(
                KGEntity.name == name.strip(),
                KGEntity.entity_type == entity_type,
            )
        )
        entity = result.scalar_one_or_none()

        if entity:
            # Update properties (merge)
            if properties:
                existing = entity.properties or {}
                existing.update(properties)
                entity.properties = existing

            # Track source document
            if source_document_id:
                sources = entity.source_documents or []
                if source_document_id not in sources:
                    sources.append(source_document_id)
                    entity.source_documents = sources

            entity.updated_at = datetime.now(timezone.utc)
            return entity.id

        # Create new entity
        entity_id = str(uuid7())
        entity = KGEntity(
            id=entity_id,
            name=name.strip(),
            entity_type=entity_type,
            properties=properties or {},
            source_documents=[source_document_id] if source_document_id else [],
        )
        self.db.add(entity)
        return entity_id

    async def upsert_relationship(
        self,
        source_name: str,
        target_name: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
        source_document_id: str | None = None,
    ) -> str | None:
        """Create or update a relationship between two entities.
        
        Entities are looked up by name. Returns relationship ID or None if
        source/target entity doesn't exist.
        """
        # Find source entity
        source_result = await self.db.execute(
            select(KGEntity).where(KGEntity.name == source_name.strip())
        )
        source_entity = source_result.scalar_one_or_none()

        # Find target entity
        target_result = await self.db.execute(
            select(KGEntity).where(KGEntity.name == target_name.strip())
        )
        target_entity = target_result.scalar_one_or_none()

        if not source_entity or not target_entity:
            logger.debug(
                "kg_relationship_skip",
                source=source_name,
                target=target_name,
                reason="entity not found",
            )
            return None

        # Check existing relationship
        result = await self.db.execute(
            select(KGRelationship).where(
                KGRelationship.source_id == source_entity.id,
                KGRelationship.target_id == target_entity.id,
                KGRelationship.relationship_type == relationship_type,
            )
        )
        rel = result.scalar_one_or_none()

        if rel:
            if properties:
                existing = rel.properties or {}
                existing.update(properties)
                rel.properties = existing
            if source_document_id:
                sources = rel.source_documents or []
                if source_document_id not in sources:
                    sources.append(source_document_id)
                    rel.source_documents = sources
            return rel.id

        # Create new relationship
        rel_id = str(uuid7())
        rel = KGRelationship(
            id=rel_id,
            source_id=source_entity.id,
            target_id=target_entity.id,
            relationship_type=relationship_type,
            properties=properties or {},
            source_documents=[source_document_id] if source_document_id else [],
        )
        self.db.add(rel)
        return rel_id

    async def get_entity(self, entity_id: str) -> KGEntity | None:
        """Fetch a single entity by ID."""
        result = await self.db.execute(
            select(KGEntity).where(KGEntity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def search_entities(
        self,
        query: str | None = None,
        entity_type: str | None = None,
        limit: int = 50,
    ) -> list[KGEntity]:
        """Search entities by name pattern and/or type."""
        stmt = select(KGEntity)
        if query:
            stmt = stmt.where(KGEntity.name.ilike(f"%{query}%"))
        if entity_type:
            stmt = stmt.where(KGEntity.entity_type == entity_type)
        stmt = stmt.order_by(KGEntity.name).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_entity_neighbors(
        self, entity_id: str, max_depth: int = 1
    ) -> dict[str, Any]:
        """Get an entity and its direct neighbors (1 or 2 hops)."""
        entity = await self.get_entity(entity_id)
        if not entity:
            return {"entity": None, "neighbors": [], "relationships": []}

        # Outgoing relationships
        out_result = await self.db.execute(
            select(KGRelationship).where(KGRelationship.source_id == entity_id)
        )
        outgoing = list(out_result.scalars().all())

        # Incoming relationships
        in_result = await self.db.execute(
            select(KGRelationship).where(KGRelationship.target_id == entity_id)
        )
        incoming = list(in_result.scalars().all())

        # Collect neighbor IDs
        neighbor_ids = set()
        for rel in outgoing:
            neighbor_ids.add(rel.target_id)
        for rel in incoming:
            neighbor_ids.add(rel.source_id)

        # Fetch neighbor entities
        neighbors = []
        if neighbor_ids:
            result = await self.db.execute(
                select(KGEntity).where(KGEntity.id.in_(neighbor_ids))
            )
            neighbors = list(result.scalars().all())

        return {
            "entity": entity,
            "neighbors": neighbors,
            "relationships": outgoing + incoming,
        }

    async def get_graph_stats(self) -> dict[str, int]:
        """Get summary statistics for the knowledge graph."""
        from sqlalchemy import func

        entity_count = (await self.db.execute(
            select(func.count()).select_from(KGEntity)
        )).scalar() or 0

        rel_count = (await self.db.execute(
            select(func.count()).select_from(KGRelationship)
        )).scalar() or 0

        type_counts_result = await self.db.execute(
            select(KGEntity.entity_type, func.count())
            .group_by(KGEntity.entity_type)
        )
        type_counts = {row[0]: row[1] for row in type_counts_result}

        return {
            "total_entities": entity_count,
            "total_relationships": rel_count,
            "entity_types": type_counts,
        }
