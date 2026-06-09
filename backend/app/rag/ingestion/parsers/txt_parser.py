"""
FinSight AI — TXT Parser
Simple text file parser.
"""

import structlog

logger = structlog.get_logger()


class TxtParser:
    """Parse plain text files."""

    async def parse(self, file_path: str) -> tuple[str, int]:
        """Extract text from a TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            page_estimate = max(1, len(content.split()) // 250)
            logger.info("txt_parsed", file=file_path, chars=len(content))
            return content, page_estimate

        except Exception as e:
            logger.error("txt_parse_error", file=file_path, error=str(e))
            raise
