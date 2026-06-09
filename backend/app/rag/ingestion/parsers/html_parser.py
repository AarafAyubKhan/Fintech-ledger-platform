"""
FinSight AI — HTML Parser
Extracts text content from HTML documents.
"""

from bs4 import BeautifulSoup
import structlog

logger = structlog.get_logger()


class HTMLParser:
    """Parse HTML documents, stripping tags and extracting text."""

    async def parse(self, file_path: str) -> tuple[str, int]:
        """Extract text from an HTML file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "lxml")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = "\n\n".join(lines)

            page_estimate = max(1, len(content.split()) // 250)
            logger.info("html_parsed", file=file_path, chars=len(content))
            return content, page_estimate

        except Exception as e:
            logger.error("html_parse_error", file=file_path, error=str(e))
            raise
