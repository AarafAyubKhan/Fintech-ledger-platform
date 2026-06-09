"""
FinSight AI — Citation Engine
Tracks, formats, and manages inline citations for LLM-generated content.
Each citation links a claim back to a specific source document and page.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class CitationRef:
    """A single citation reference."""
    id: str
    source: str
    page: int | None = None
    chunk_id: str | None = None
    content_preview: str = ""
    relevance_score: float = 0.0
    document_id: str = ""
    document_type: str = ""

    def to_inline(self) -> str:
        """Format as inline citation string."""
        if self.page:
            return f"[{self.source}, Page {self.page}]"
        return f"[{self.source}]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "content_preview": self.content_preview,
            "relevance_score": self.relevance_score,
            "document_id": self.document_id,
            "document_type": self.document_type,
        }


class CitationEngine:
    """Manages citation tracking, formatting, and numbering for reports."""

    def __init__(self):
        self._citations: list[CitationRef] = []
        self._source_index: dict[str, int] = {}  # source -> citation number

    def add_citation(
        self,
        source: str,
        page: int | None = None,
        chunk_id: str | None = None,
        content_preview: str = "",
        relevance_score: float = 0.0,
        document_id: str = "",
        document_type: str = "",
    ) -> CitationRef:
        """Add a citation and return the CitationRef."""
        from uuid6 import uuid7

        citation = CitationRef(
            id=str(uuid7()),
            source=source,
            page=page,
            chunk_id=chunk_id,
            content_preview=content_preview[:500],
            relevance_score=relevance_score,
            document_id=document_id,
            document_type=document_type,
        )
        self._citations.append(citation)

        # Assign citation number
        key = f"{source}:{page}" if page else source
        if key not in self._source_index:
            self._source_index[key] = len(self._source_index) + 1

        return citation

    def from_retrieved_chunks(
        self, chunks: list[dict[str, Any]]
    ) -> list[CitationRef]:
        """Build citations from a list of retrieved document chunks."""
        citations = []
        for chunk in chunks:
            payload = chunk.get("payload", chunk)
            citation = self.add_citation(
                source=payload.get("document_title", payload.get("source", "Unknown")),
                page=payload.get("page_number"),
                chunk_id=payload.get("chunk_id", chunk.get("id", "")),
                content_preview=payload.get("content", "")[:300],
                relevance_score=chunk.get("score", 0.0),
                document_id=payload.get("document_id", ""),
                document_type=payload.get("document_type", ""),
            )
            citations.append(citation)
        return citations

    def get_citation_number(self, citation: CitationRef) -> int:
        """Get the sequential number for a citation."""
        key = f"{citation.source}:{citation.page}" if citation.page else citation.source
        return self._source_index.get(key, 0)

    def format_inline(self, citation: CitationRef) -> str:
        """Format a citation as an inline reference."""
        num = self.get_citation_number(citation)
        return f"[{num}]" if num else citation.to_inline()

    def format_bibliography(self) -> str:
        """Generate a numbered bibliography from all citations."""
        if not self._citations:
            return ""

        # Deduplicate by source+page
        seen = set()
        unique_citations = []
        for c in self._citations:
            key = f"{c.source}:{c.page}"
            if key not in seen:
                seen.add(key)
                unique_citations.append(c)

        lines = ["## Sources\n"]
        for i, citation in enumerate(unique_citations, 1):
            line = f"{i}. **{citation.source}**"
            if citation.page:
                line += f", Page {citation.page}"
            if citation.document_type:
                line += f" ({citation.document_type})"
            lines.append(line)

        return "\n".join(lines)

    def inject_citations_into_text(
        self,
        text: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> str:
        """Add inline citations to LLM-generated text based on content matching.
        
        Simple heuristic: if a retrieved chunk's content appears as a substring
        in the generated text, append an inline citation.
        """
        citations = self.from_retrieved_chunks(retrieved_chunks)

        for citation in citations:
            preview = citation.content_preview[:100].strip()
            if preview and preview in text:
                inline = self.format_inline(citation)
                text = text.replace(preview, f"{preview} {inline}", 1)

        return text

    def get_all_citations(self) -> list[dict[str, Any]]:
        """Return all citations as dicts for API responses."""
        return [c.to_dict() for c in self._citations]

    def get_unique_sources(self) -> list[str]:
        """Return deduplicated list of source names."""
        return list(dict.fromkeys(c.source for c in self._citations))

    @property
    def count(self) -> int:
        """Total number of citations tracked."""
        return len(self._citations)
