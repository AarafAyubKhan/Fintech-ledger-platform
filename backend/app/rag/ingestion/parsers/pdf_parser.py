"""
FinSight AI — PDF Parser
Extracts text and tables from PDF files using PyMuPDF.
"""

import fitz  # PyMuPDF
import structlog

logger = structlog.get_logger()


class PDFParser:
    """Parse PDF documents with table extraction support."""

    async def parse(self, file_path: str) -> tuple[str, int]:
        """
        Extract text from a PDF file.
        
        Returns:
            tuple of (extracted_text, page_count)
        """
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            text_parts = []

            for page_num in range(page_count):
                page = doc[page_num]

                # Extract text
                text = page.get_text("text")
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")

                # Extract tables as text
                tables = page.find_tables()
                if tables and tables.tables:
                    for table in tables.tables:
                        try:
                            table_data = table.extract()
                            if table_data:
                                table_text = self._format_table(table_data)
                                text_parts.append(f"[Table on Page {page_num + 1}]\n{table_text}")
                        except Exception:
                            pass

            doc.close()

            full_text = "\n\n".join(text_parts)
            logger.info("pdf_parsed", file=file_path, pages=page_count, chars=len(full_text))
            return full_text, page_count

        except Exception as e:
            logger.error("pdf_parse_error", file=file_path, error=str(e))
            raise

    def _format_table(self, table_data: list[list]) -> str:
        """Format extracted table data as readable text."""
        if not table_data:
            return ""

        lines = []
        for row in table_data:
            cells = [str(cell).strip() if cell else "" for cell in row]
            lines.append(" | ".join(cells))

        return "\n".join(lines)
