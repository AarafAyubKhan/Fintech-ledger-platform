"""
FinSight AI — Knowledge Graph Tests
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.knowledge_graph.graph_store import KnowledgeGraphStore


@pytest.mark.asyncio
class TestKnowledgeGraphStore:
    """Tests for the KnowledgeGraphStore."""

    async def test_upsert_entity(self, db_session: AsyncSession):
        """Test creating a new entity."""
        store = KnowledgeGraphStore(db_session)
        entity_id = await store.upsert_entity(
            name="HDFC Bank",
            entity_type="COMPANY",
            properties={"sector": "Banking"},
            source_document_id="doc-1",
        )

        assert entity_id
        entity = await store.get_entity(entity_id)
        assert entity is not None
        assert entity.name == "HDFC Bank"
        assert entity.entity_type == "COMPANY"

    async def test_upsert_entity_merge(self, db_session: AsyncSession):
        """Test that upserting an existing entity merges properties."""
        store = KnowledgeGraphStore(db_session)

        id1 = await store.upsert_entity(
            name="HDFC Bank", entity_type="COMPANY",
            properties={"sector": "Banking"},
        )
        id2 = await store.upsert_entity(
            name="HDFC Bank", entity_type="COMPANY",
            properties={"exchange": "NSE"},
        )

        assert id1 == id2
        entity = await store.get_entity(id1)
        assert entity.properties.get("sector") == "Banking"
        assert entity.properties.get("exchange") == "NSE"

    async def test_upsert_relationship(self, db_session: AsyncSession):
        """Test creating a relationship between entities."""
        store = KnowledgeGraphStore(db_session)

        await store.upsert_entity(name="HDFC Bank", entity_type="COMPANY")
        await store.upsert_entity(name="Banking Sector", entity_type="INDUSTRY")

        rel_id = await store.upsert_relationship(
            source_name="HDFC Bank",
            target_name="Banking Sector",
            relationship_type="BELONGS_TO",
        )

        assert rel_id is not None

    async def test_relationship_missing_entity(self, db_session: AsyncSession):
        """Test that relationship with missing entity returns None."""
        store = KnowledgeGraphStore(db_session)

        await store.upsert_entity(name="HDFC Bank", entity_type="COMPANY")

        rel_id = await store.upsert_relationship(
            source_name="HDFC Bank",
            target_name="Nonexistent Entity",
            relationship_type="BELONGS_TO",
        )

        assert rel_id is None

    async def test_search_entities(self, db_session: AsyncSession):
        """Test searching entities by name."""
        store = KnowledgeGraphStore(db_session)

        await store.upsert_entity(name="HDFC Bank", entity_type="COMPANY")
        await store.upsert_entity(name="ICICI Bank", entity_type="COMPANY")
        await store.upsert_entity(name="Banking Sector", entity_type="INDUSTRY")

        results = await store.search_entities(query="Bank")
        assert len(results) >= 2

    async def test_search_entities_by_type(self, db_session: AsyncSession):
        """Test filtering entity search by type."""
        store = KnowledgeGraphStore(db_session)

        await store.upsert_entity(name="HDFC Bank", entity_type="COMPANY")
        await store.upsert_entity(name="Banking Sector", entity_type="INDUSTRY")

        results = await store.search_entities(entity_type="COMPANY")
        assert len(results) == 1
        assert results[0].name == "HDFC Bank"

    async def test_get_entity_neighbors(self, db_session: AsyncSession):
        """Test getting entity with its neighbors."""
        store = KnowledgeGraphStore(db_session)

        await store.upsert_entity(name="HDFC Bank", entity_type="COMPANY")
        await store.upsert_entity(name="Banking", entity_type="INDUSTRY")
        await store.upsert_relationship(
            source_name="HDFC Bank", target_name="Banking",
            relationship_type="BELONGS_TO",
        )

        entity_id = (await store.search_entities(query="HDFC"))[0].id
        data = await store.get_entity_neighbors(entity_id)

        assert data["entity"] is not None
        assert len(data["neighbors"]) >= 1
        assert len(data["relationships"]) >= 1

    async def test_graph_stats(self, db_session: AsyncSession):
        """Test getting graph statistics."""
        store = KnowledgeGraphStore(db_session)

        await store.upsert_entity(name="Entity A", entity_type="COMPANY")
        await store.upsert_entity(name="Entity B", entity_type="INDUSTRY")

        stats = await store.get_graph_stats()
        assert stats["total_entities"] >= 2
        assert "COMPANY" in stats["entity_types"]

    async def test_empty_name_skipped(self, db_session: AsyncSession):
        """Test that empty entity names are skipped."""
        store = KnowledgeGraphStore(db_session)
        entity_id = await store.upsert_entity(
            name="  ", entity_type="COMPANY",
        )
        assert entity_id == ""
