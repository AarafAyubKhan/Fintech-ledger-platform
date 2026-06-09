"""
FinSight AI — RAG Ingestion Pipeline
Main orchestrator for the document ingestion workflow:
Parse → Chunk → Embed → Store in Qdrant.
"""

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.config import get_settings
from app.models.document import Document, DocumentChunk, DocumentStatus

logger = structlog.get_logger()
settings = get_settings()


class IngestionPipeline:
    """Orchestrates the full document ingestion workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest(self, document: Document) -> dict[str, Any]:
        """Run the full ingestion pipeline for a document.
        
        Steps:
            1. Parse document content (PDF/DOCX/HTML/TXT)
            2. Chunk content with metadata
            3. Generate embeddings
            4. Upsert into Qdrant vector store
            5. Extract entities for knowledge graph (optional)
        
        Returns:
            Dict with ingestion stats (pages, chunks, embeddings).
        
        Raises:
            IngestionError: If any step in the pipeline fails.
        """
        pipeline_start = datetime.now(timezone.utc)
        stats: dict[str, Any] = {
            "document_id": document.id,
            "status": "processing",
            "pages": 0,
            "chunks": 0,
            "embeddings": 0,
            "errors": [],
        }

        logger.info(
            "ingestion_pipeline_started",
            doc_id=document.id,
            file_type=document.file_type.value,
            file_name=document.file_name,
        )

        try:
            # ── Step 1: Parse ─────────────────────────────────
            content, page_count = await self._parse(document)
            stats["pages"] = page_count
            logger.info("parse_complete", doc_id=document.id, pages=page_count)

            # ── Step 2: Chunk ─────────────────────────────────
            chunks = await self._chunk(content, document)
            stats["chunks"] = len(chunks)
            logger.info("chunking_complete", doc_id=document.id, chunks=len(chunks))

            # ── Step 3: Embed & Store ─────────────────────────
            embedded_count = await self._embed_and_store(chunks, document)
            stats["embeddings"] = embedded_count
            logger.info("embedding_complete", doc_id=document.id, embeddings=embedded_count)

            # ── Step 4: Knowledge Graph (optional) ────────────
            try:
                await self._extract_knowledge_graph(content, document)
            except Exception as kg_err:
                # Knowledge graph is non-critical; log and continue
                stats["errors"].append(f"Knowledge graph extraction: {str(kg_err)}")
                logger.warning("kg_extraction_failed", doc_id=document.id, error=str(kg_err))

            # ── Update document record ────────────────────────
            document.page_count = page_count
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.COMPLETED
            document.processed_at = datetime.now(timezone.utc)
            stats["status"] = "completed"

        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.processing_error = str(e)
            stats["status"] = "failed"
            stats["errors"].append(str(e))
            logger.error("ingestion_pipeline_failed", doc_id=document.id, error=str(e))
            raise

        finally:
            elapsed = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
            stats["duration_seconds"] = round(elapsed, 2)
            logger.info(
                "ingestion_pipeline_finished",
                doc_id=document.id,
                status=stats["status"],
                duration_s=stats["duration_seconds"],
            )

        return stats

    async def _parse(self, document: Document) -> tuple[str, int]:
        """Parse raw document into text content."""
        from app.rag.ingestion.parsers.pdf_parser import PDFParser
        from app.rag.ingestion.parsers.docx_parser import DocxParser
        from app.rag.ingestion.parsers.txt_parser import TxtParser
        from app.rag.ingestion.parsers.html_parser import HTMLParser

        parsers = {
            "pdf": PDFParser(),
            "docx": DocxParser(),
            "txt": TxtParser(),
            "html": HTMLParser(),
        }

        parser = parsers.get(document.file_type.value)
        if not parser:
            raise ValueError(f"No parser for file type: {document.file_type.value}")

        return await parser.parse(document.file_path)

    async def _chunk(self, content: str, document: Document) -> list[DocumentChunk]:
        """Split content into chunks and persist as DB records."""
        from app.rag.ingestion.chunker import RecursiveChunker

        chunker = RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        text_chunks = chunker.chunk(content)
        db_chunks: list[DocumentChunk] = []

        for i, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                id=str(uuid7()),
                document_id=document.id,
                chunk_index=i,
                content=chunk_text.text,
                page_number=chunk_text.page_number,
                char_count=len(chunk_text.text),
                chunk_metadata={
                    "document_title": document.title,
                    "document_type": document.document_type.value,
                    "company_id": document.company_id,
                    "source": document.file_name,
                },
            )
            self.db.add(chunk)
            db_chunks.append(chunk)

        return db_chunks

    async def _embed_and_store(
        self, chunks: list[DocumentChunk], document: Document
    ) -> int:
        """Generate embeddings and upsert into Qdrant."""
        from app.rag.embeddings.provider import get_embedding_provider
        from app.rag.retrieval.vector_search import QdrantVectorStore

        embedding_provider = get_embedding_provider()
        vector_store = QdrantVectorStore()
        embedded = 0

        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]

            embeddings = await embedding_provider.embed_documents(texts)

            points = []
            for chunk, embedding in zip(batch, embeddings):
                point_id = chunk.id
                chunk.qdrant_point_id = point_id
                chunk.embedding_model = embedding_provider.model_name

                points.append({
                    "id": point_id,
                    "vector": embedding,
                    "payload": {
                        "document_id": document.id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "document_title": document.title,
                        "document_type": document.document_type.value,
                        "company_id": document.company_id,
                        "file_name": document.file_name,
                    },
                })

            await vector_store.upsert_points(points)
            embedded += len(batch)

        return embedded

    async def _extract_knowledge_graph(
        self, content: str, document: Document
    ) -> None:
        """Extract entities and relationships for the knowledge graph."""
        from app.rag.knowledge_graph.extractor import KnowledgeGraphExtractor

        extractor = KnowledgeGraphExtractor(self.db)
        await extractor.extract_from_document(
            content=content,
            document_id=document.id,
            document_title=document.title,
        )

    async def reprocess_document(self, document: Document) -> dict[str, Any]:
        """Re-run ingestion for a previously processed document.
        
        Clears existing chunks and re-ingests from scratch.
        """
        from sqlalchemy import delete

        # Delete existing chunks
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )

        # Reset document status
        document.status = DocumentStatus.PROCESSING
        document.processing_error = None
        document.chunk_count = None
        document.processed_at = None

        # Re-run pipeline
        return await self.ingest(document)
