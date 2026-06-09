"""
FinSight AI — Citation Validation Tests
"""

import pytest
from app.rag.citations.validator import CitationValidator
from app.rag.citations.engine import CitationEngine


class TestCitationValidator:
    """Tests for the CitationValidator."""

    def setup_method(self):
        self.chunks = [
            {
                "payload": {
                    "content": "HDFC Bank reported a net profit of ₹16,372 crore in FY2024.",
                    "document_title": "HDFC Bank Annual Report FY2024",
                    "page_number": 45,
                    "source": "HDFC Bank AR",
                }
            },
            {
                "payload": {
                    "content": "The bank's net interest margin stood at 3.6% for the year.",
                    "document_title": "HDFC Bank Annual Report FY2024",
                    "page_number": 52,
                    "source": "HDFC Bank AR",
                }
            },
        ]

    def test_valid_citation_passes(self):
        """Test that text with valid citations passes validation."""
        validator = CitationValidator(self.chunks)
        text = "HDFC Bank's net profit was strong [HDFC Bank Annual Report FY2024, Page 45]."
        result = validator.validate_response(text)

        assert result["valid_citations"] >= 1

    def test_ungrounded_citation_flagged(self):
        """Test that citations referencing nonexistent sources are flagged."""
        validator = CitationValidator(self.chunks)
        text = "Revenue grew 25% [Fake Document, Page 99]."
        result = validator.validate_response(text)

        assert len(result["invalid_citations"]) > 0

    def test_grounding_score_high_for_grounded_text(self):
        """Test grounding score is high when text matches source content."""
        validator = CitationValidator(self.chunks)
        text = "HDFC Bank reported a net profit and the net interest margin stood at 3.6%."
        result = validator.validate_response(text)

        assert result["grounding_score"] > 0.1

    def test_grounding_score_low_for_unrelated_text(self):
        """Test grounding score is low for completely unrelated text."""
        validator = CitationValidator(self.chunks)
        text = "The weather in Tokyo was sunny yesterday with temperatures reaching 35 degrees."
        result = validator.validate_response(text)

        assert result["grounding_score"] < 0.3

    def test_empty_text(self):
        """Test validation of empty text."""
        validator = CitationValidator(self.chunks)
        result = validator.validate_response("")

        assert result["total_inline_citations"] == 0

    def test_numbered_citations_valid(self):
        """Test that numbered citations [1], [2] are considered valid."""
        validator = CitationValidator(self.chunks)
        text = "The profit was high [1] and margins improved [2]."
        result = validator.validate_response(text)

        assert result["valid_citations"] == 2


class TestCitationEngine:
    """Tests for the CitationEngine."""

    def test_add_citation(self):
        """Test adding a citation."""
        engine = CitationEngine()
        citation = engine.add_citation(
            source="HDFC Bank Annual Report",
            page=45,
            content_preview="Net profit was ₹16,372 crore",
        )

        assert citation.source == "HDFC Bank Annual Report"
        assert citation.page == 45
        assert engine.count == 1

    def test_bibliography_generation(self):
        """Test generating a bibliography."""
        engine = CitationEngine()
        engine.add_citation(source="Report A", page=10)
        engine.add_citation(source="Report B", page=20)

        bib = engine.format_bibliography()
        assert "Report A" in bib
        assert "Report B" in bib
        assert "## Sources" in bib

    def test_unique_sources(self):
        """Test getting unique source names."""
        engine = CitationEngine()
        engine.add_citation(source="Report A")
        engine.add_citation(source="Report A")
        engine.add_citation(source="Report B")

        unique = engine.get_unique_sources()
        assert len(unique) == 2

    def test_from_retrieved_chunks(self):
        """Test building citations from retrieved chunks."""
        engine = CitationEngine()
        chunks = [
            {"payload": {"document_title": "Doc A", "page_number": 1, "content": "text"}},
            {"payload": {"document_title": "Doc B", "page_number": 5, "content": "more"}},
        ]

        citations = engine.from_retrieved_chunks(chunks)
        assert len(citations) == 2
        assert engine.count == 2
