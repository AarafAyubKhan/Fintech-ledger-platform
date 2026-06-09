"""
FinSight AI — Document Service
Business logic for document processing and ingestion.
"""

import os
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.models.document import Document, DocumentChunk, DocumentStatus

logger = structlog.get_logger()


class DocumentService:
    """Handles document processing and RAG ingestion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_document(self, document: Document) -> None:
        """Process a document through the full ingestion pipeline."""
        logger.info("ingestion_started", doc_id=document.id, file_type=document.file_type.value)

        try:
            # 1. Parse the document
            content, page_count = await self._parse_document(document)

            # 2. Chunk the content
            chunks = await self._chunk_content(content, document)

            # 3. Generate embeddings and store in Qdrant
            await self._embed_and_store(chunks, document)

            # 4. Update document metadata
            document.page_count = page_count
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.COMPLETED
            document.processed_at = datetime.now(timezone.utc)

            logger.info(
                "ingestion_completed",
                doc_id=document.id,
                pages=page_count,
                chunks=len(chunks),
            )

        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.processing_error = str(e)
            logger.error("ingestion_failed", doc_id=document.id, error=str(e))
            raise

    async def _parse_document(self, document: Document) -> tuple[str, int]:
        """Parse document content based on file type."""
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
            raise ValueError(f"No parser available for file type: {document.file_type}")

        return await parser.parse(document.file_path)

    async def _chunk_content(
        self, content: str, document: Document
    ) -> list[DocumentChunk]:
        """Split content into chunks and create database records."""
        from app.rag.ingestion.chunker import RecursiveChunker
        from app.config import get_settings

        settings = get_settings()
        chunker = RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        text_chunks = chunker.chunk(content)
        db_chunks = []

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
    ) -> None:
        """Generate embeddings and store in Qdrant."""
        from app.rag.embeddings.provider import get_embedding_provider
        from app.rag.retrieval.vector_search import QdrantVectorStore

        embedding_provider = get_embedding_provider()
        vector_store = QdrantVectorStore()

        # Generate embeddings in batches
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]

            embeddings = await embedding_provider.embed_documents(texts)

            # Store in Qdrant with metadata
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

        logger.info(
            "embeddings_stored",
            doc_id=document.id,
            total_chunks=len(chunks),
        )
