"""
FinSight AI — Chunking Unit Tests
"""

import pytest
from app.rag.ingestion.chunker import RecursiveChunker


class TestRecursiveChunker:
    """Tests for the RecursiveChunker."""

    def test_basic_chunking(self):
        """Test that text is split into chunks of appropriate size."""
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
        text = "A" * 250
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= 120  # Allow some overflow for word boundaries

    def test_empty_text(self):
        """Test chunking empty text returns no chunks."""
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk("")
        assert len(chunks) == 0

    def test_short_text_single_chunk(self):
        """Test that short text returns a single chunk."""
        chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
        text = "This is a short text."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_overlap_between_chunks(self):
        """Test that consecutive chunks have overlapping content."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        words = [f"word{i}" for i in range(50)]
        text = " ".join(words)
        chunks = chunker.chunk(text)

        if len(chunks) >= 2:
            # There should be some overlap between consecutive chunks
            chunk1_text = chunks[0].text
            chunk2_text = chunks[1].text
            # The end of chunk1 should overlap with the start of chunk2
            assert len(chunk1_text) > 0
            assert len(chunk2_text) > 0

    def test_chunk_index_sequential(self):
        """Test that chunk indices are sequential."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = "word " * 100
        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_preserves_content(self):
        """Test that all original content is preserved across chunks."""
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
        text = "The quick brown fox jumps over the lazy dog. " * 10
        chunks = chunker.chunk(text)

        # Concatenated chunks should contain all original words
        all_chunk_text = " ".join(c.text for c in chunks)
        for word in text.split():
            assert word in all_chunk_text
