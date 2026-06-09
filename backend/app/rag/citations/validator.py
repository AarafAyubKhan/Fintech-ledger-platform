"""
FinSight AI — Citation Validator
Validates that LLM-generated citations are grounded in actual retrieved content.
Detects hallucinated sources and ungrounded claims.
"""

import re
from typing import Any

import structlog

logger = structlog.get_logger()


class CitationValidator:
    """Validates citations in LLM output against retrieved source chunks."""

    def __init__(self, retrieved_chunks: list[dict[str, Any]]):
        self.chunks = retrieved_chunks
        self._chunk_contents: list[str] = []
        self._chunk_sources: set[str] = set()
        self._index_chunks()

    def _index_chunks(self) -> None:
        """Index chunk contents and source names for fast lookup."""
        for chunk in self.chunks:
            payload = chunk.get("payload", chunk)
            content = payload.get("content", "")
            self._chunk_contents.append(content.lower())

            source = payload.get("document_title", payload.get("source", ""))
            if source:
                self._chunk_sources.add(source.lower())

    def validate_response(
        self, text: str, claimed_citations: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Validate an LLM response for citation accuracy.
        
        Checks:
        1. Inline citations reference real sources
        2. Key claims have supporting evidence in retrieved chunks
        3. No hallucinated sources
        
        Args:
            text: The LLM-generated response text.
            claimed_citations: Optional list of explicit citation objects.
        
        Returns:
            Validation result dict with is_valid, issues, score, etc.
        """
        issues: list[str] = []
        warnings: list[str] = []

        # 1. Extract inline citations from text
        inline_citations = self._extract_inline_citations(text)

        # 2. Validate each inline citation
        valid_citations = 0
        invalid_citations = []

        for cite_text in inline_citations:
            if self._is_citation_grounded(cite_text):
                valid_citations += 1
            else:
                invalid_citations.append(cite_text)
                issues.append(f"Ungrounded citation: {cite_text}")

        # 3. Validate explicit citation objects
        if claimed_citations:
            for citation in claimed_citations:
                source = citation.get("source", "")
                if source and source.lower() not in self._chunk_sources:
                    issues.append(f"Citation source not in retrieved documents: {source}")

        # 4. Check for hallucinated numerical claims
        hallucinated_numbers = self._check_numerical_claims(text)
        for claim in hallucinated_numbers:
            warnings.append(f"Unverifiable numerical claim: {claim}")

        # 5. Calculate confidence score
        total_citations = len(inline_citations)
        if total_citations > 0:
            citation_accuracy = valid_citations / total_citations
        else:
            citation_accuracy = 1.0 if not claimed_citations else 0.5

        # Overall grounding score
        grounding_score = self._calculate_grounding_score(text)

        is_valid = len(issues) == 0 and grounding_score >= 0.3

        result = {
            "is_valid": is_valid,
            "confidence_score": round(min(citation_accuracy, grounding_score), 3),
            "citation_accuracy": round(citation_accuracy, 3),
            "grounding_score": round(grounding_score, 3),
            "total_inline_citations": total_citations,
            "valid_citations": valid_citations,
            "invalid_citations": invalid_citations,
            "issues": issues,
            "warnings": warnings,
            "suggestions": self._generate_suggestions(issues, warnings, grounding_score),
        }

        logger.info(
            "citation_validation_complete",
            is_valid=is_valid,
            confidence=result["confidence_score"],
            issues=len(issues),
        )

        return result

    def _extract_inline_citations(self, text: str) -> list[str]:
        """Extract inline citations like [Source Name, Page X] from text."""
        # Match patterns like [Source Title], [Source, Page 5], [1], [2]
        pattern = r"\[([^\]]+)\]"
        matches = re.findall(pattern, text)

        # Filter out non-citation brackets (e.g., code, markdown links)
        citations = []
        for match in matches:
            # Skip if it's a URL or code
            if match.startswith("http") or match.startswith("!"):
                continue
            # Skip single characters that are likely markdown
            if len(match) <= 1 and not match.isdigit():
                continue
            citations.append(match)

        return citations

    def _is_citation_grounded(self, citation_text: str) -> bool:
        """Check if a citation reference exists in retrieved sources."""
        citation_lower = citation_text.lower()

        # Check if it's a numbered citation (always valid if we have chunks)
        if citation_lower.strip().isdigit():
            num = int(citation_lower.strip())
            return num <= len(self.chunks)

        # Check source name match
        for source in self._chunk_sources:
            if source in citation_lower or citation_lower in source:
                return True

        # Fuzzy: check if any significant words match
        cite_words = set(citation_lower.split()) - {"page", "the", "of", "and", "in", "a"}
        for source in self._chunk_sources:
            source_words = set(source.split())
            if cite_words & source_words:
                return True

        return False

    def _check_numerical_claims(self, text: str) -> list[str]:
        """Find numerical claims that can't be verified in source chunks."""
        # Find percentage and currency patterns
        patterns = [
            r"(\d+\.?\d*%)",  # Percentages
            r"(₹[\d,]+\s*(?:crore|lakh|billion|million)?)",  # INR amounts
            r"(\$[\d,]+\s*(?:billion|million|thousand)?)",  # USD amounts
            r"(Rs\.?\s*[\d,]+\s*(?:crore|lakh)?)",  # Rs amounts
        ]

        unverified = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Check if this number appears in any chunk
                found = any(match.lower() in content for content in self._chunk_contents)
                if not found:
                    unverified.append(match)

        return unverified[:5]  # Limit to top 5

    def _calculate_grounding_score(self, text: str) -> float:
        """Calculate how well the response is grounded in retrieved content.
        
        Uses simple token overlap between response and source chunks.
        """
        if not self._chunk_contents or not text:
            return 0.0

        text_lower = text.lower()
        text_tokens = set(text_lower.split())

        # Combine all chunk content
        all_chunk_tokens = set()
        for content in self._chunk_contents:
            all_chunk_tokens.update(content.split())

        # Remove common stopwords for meaningful comparison
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "and",
            "but", "or", "nor", "not", "so", "yet", "both", "either",
            "neither", "this", "that", "these", "those", "it", "its",
        }

        meaningful_text_tokens = text_tokens - stopwords
        meaningful_chunk_tokens = all_chunk_tokens - stopwords

        if not meaningful_text_tokens:
            return 0.0

        overlap = meaningful_text_tokens & meaningful_chunk_tokens
        return len(overlap) / len(meaningful_text_tokens)

    def _generate_suggestions(
        self,
        issues: list[str],
        warnings: list[str],
        grounding_score: float,
    ) -> list[str]:
        """Generate improvement suggestions based on validation results."""
        suggestions = []

        if issues:
            suggestions.append(
                "Some citations reference sources not found in the knowledge base. "
                "Consider re-running retrieval with broader search terms."
            )

        if grounding_score < 0.3:
            suggestions.append(
                "Response has low grounding in source documents. "
                "The agent may need more context — try uploading additional documents."
            )

        if warnings:
            suggestions.append(
                "Some numerical claims could not be verified against source documents. "
                "These should be manually verified before inclusion in reports."
            )

        if not issues and not warnings and grounding_score >= 0.5:
            suggestions.append("Response is well-grounded with valid citations.")

        return suggestions
