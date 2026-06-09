"""
FinSight AI — Document Chunking
Recursive and semantic chunking for RAG pipeline.
"""

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    text: str
    page_number: int | None = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0


class RecursiveChunker:
    """
    Recursive character text splitter with configurable size and overlap.
    Splits on paragraph → sentence → word boundaries progressively.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", ", ", " ", ""]

    def chunk(self, text: str) -> list[TextChunk]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []

        # Extract page markers for citation tracking
        page_map = self._build_page_map(text)

        # Split recursively
        raw_chunks = self._split_recursive(text, self.separators)

        # Create TextChunk objects with metadata
        chunks = []
        char_offset = 0

        for i, chunk_text in enumerate(raw_chunks):
            page_num = self._get_page_number(char_offset, page_map)
            chunks.append(TextChunk(
                text=chunk_text.strip(),
                page_number=page_num,
                chunk_index=i,
                start_char=char_offset,
                end_char=char_offset + len(chunk_text),
            ))
            char_offset += len(chunk_text) - self.chunk_overlap

        logger.info("chunking_complete", total_chunks=len(chunks), text_length=len(text))
        return chunks

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using progressively finer separators."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # Try each separator
        for sep in separators:
            if sep and sep in text:
                parts = text.split(sep)
                chunks = []
                current_chunk = ""

                for part in parts:
                    candidate = current_chunk + sep + part if current_chunk else part

                    if len(candidate) <= self.chunk_size:
                        current_chunk = candidate
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part

                if current_chunk:
                    chunks.append(current_chunk)

                # Apply overlap
                if self.chunk_overlap > 0:
                    chunks = self._apply_overlap(chunks)

                return chunks

        # Fallback: hard split by character count
        return [
            text[i : i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
        ]

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between adjacent chunks."""
        if len(chunks) <= 1:
            return chunks

        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_end = chunks[i - 1][-self.chunk_overlap :] if len(chunks[i - 1]) > self.chunk_overlap else chunks[i - 1]
            overlapped.append(prev_end + chunks[i])

        return overlapped

    def _build_page_map(self, text: str) -> list[tuple[int, int]]:
        """Build a mapping of character offsets to page numbers."""
        page_map = []
        pattern = re.compile(r'\[Page (\d+)\]')
        for match in pattern.finditer(text):
            page_map.append((match.start(), int(match.group(1))))
        return page_map

    def _get_page_number(self, char_offset: int, page_map: list[tuple[int, int]]) -> int | None:
        """Get the page number for a given character offset."""
        if not page_map:
            return None
        for pos, page in reversed(page_map):
            if char_offset >= pos:
                return page
        return page_map[0][1] if page_map else None


class SemanticChunker:
    """
    Semantic chunking based on embedding similarity.
    Splits at natural semantic boundaries where topic shifts occur.
    """

    def __init__(self, similarity_threshold: float = 0.75, chunk_size: int = 1000):
        self.similarity_threshold = similarity_threshold
        self.chunk_size = chunk_size

    async def chunk(self, text: str) -> list[TextChunk]:
        """Split text at semantic boundaries."""
        # First, split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 3:
            return [TextChunk(text=text, chunk_index=0)]

        # Get embeddings for each sentence
        from app.rag.embeddings.provider import get_embedding_provider
        embedding_provider = get_embedding_provider()

        embeddings = await embedding_provider.embed_documents(sentences)

        # Find semantic boundaries using cosine similarity
        import numpy as np

        boundaries = [0]
        for i in range(1, len(embeddings)):
            sim = np.dot(embeddings[i - 1], embeddings[i]) / (
                np.linalg.norm(embeddings[i - 1]) * np.linalg.norm(embeddings[i])
            )
            if sim < self.similarity_threshold:
                boundaries.append(i)
        boundaries.append(len(sentences))

        # Build chunks from semantic segments
        chunks = []
        for i in range(len(boundaries) - 1):
            chunk_sentences = sentences[boundaries[i] : boundaries[i + 1]]
            chunk_text = " ".join(chunk_sentences)

            # Split further if chunk is too large
            if len(chunk_text) > self.chunk_size * 1.5:
                sub_chunker = RecursiveChunker(self.chunk_size, 100)
                sub_chunks = sub_chunker.chunk(chunk_text)
                for sc in sub_chunks:
                    sc.chunk_index = len(chunks)
                    chunks.append(sc)
            else:
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_index=len(chunks),
                ))

        return chunks
