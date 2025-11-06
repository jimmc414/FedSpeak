"""
Text extraction module for FedSpeak.
Extracts clean text from HTML and PDF Fed documents.

Based on:
- Document 01 Section 2 (extraction methods)
- Architecture Section 3.2 (Text Extractor design)
- Requirements REQ-TP-001 to REQ-TP-007
"""

from bs4 import BeautifulSoup
import pdfplumber
import re
import logging
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of text extraction operation."""
    success: bool
    text: str = ""
    word_count: int = 0
    format: str = "html"  # 'html' or 'pdf'
    error: Optional[str] = None
    metadata: Dict = None


class TextExtractor:
    """
    Extracts text from Fed documents.

    Handles format evolution:
    - Modern format (2013+): <div id="article">
    - Legacy format (2008-2012): <div id="leftText">
    - Historical format (1994-2007): <div id="generalContentText">
    - Ultimate fallback: <body> (handles all pre-2000 formats)

    The cascading selector approach automatically handles all Fed website
    versions from 1994 onwards.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize extractor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.min_word_count_statement = self.config.get('validation', {}).get('min_word_count_statement', 100)
        self.min_word_count_minutes = self.config.get('validation', {}).get('min_word_count_minutes', 1000)

    def extract(self, filepath: Path, doc_type: str = 'policy_statement') -> ExtractionResult:
        """
        Extract text from document (auto-detect format).

        Args:
            filepath: Path to document file
            doc_type: 'policy_statement' or 'fomc_minutes'

        Returns:
            ExtractionResult with extracted text
        """
        if not filepath.exists():
            return ExtractionResult(
                success=False,
                error=f"File not found: {filepath}"
            )

        # Detect format from extension
        if filepath.suffix.lower() == '.pdf':
            return self.extract_pdf(filepath)
        else:
            return self.extract_html(filepath, doc_type)

    def extract_html(self, filepath: Path, doc_type: str = 'policy_statement') -> ExtractionResult:
        """
        Extract text from HTML document with version-aware parsing.

        Algorithm (from Document 01, Section 2.1):
        1. Parse HTML with BeautifulSoup + lxml
        2. Remove script, style, nav, footer, header tags
        3. Try cascading selectors: article → leftText → generalContentText → body
        4. Extract text with newline preservation
        5. Clean whitespace
        6. Validate word count

        Args:
            filepath: Path to HTML file
            doc_type: Document type for validation

        Returns:
            ExtractionResult with extracted text
        """
        try:
            # Read HTML file
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Parse with BeautifulSoup + lxml (fast C-based parser)
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove noise elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            # Version-aware content detection with cascading fallback
            # Try modern format first (2013+)
            main_content = soup.find('div', {'id': 'article'})

            if not main_content:
                # Try legacy format (2008-2012)
                main_content = soup.find('div', {'id': 'leftText'})

            if not main_content:
                # Try alternative container
                main_content = soup.find('div', {'id': 'generalContentText'})

            if not main_content:
                # Ultimate fallback - use body
                main_content = soup.body

            if not main_content:
                return ExtractionResult(
                    success=False,
                    error="Could not find main content in HTML"
                )

            # Extract text with newline preservation
            text = main_content.get_text(separator='\n', strip=True)

            # Clean whitespace
            text = self._clean_text(text)

            # Remove boilerplate
            text = self._remove_boilerplate(text)

            # Calculate word count
            word_count = len(text.split())

            # Validate extraction
            min_words = (self.min_word_count_minutes if doc_type == 'fomc_minutes'
                        else self.min_word_count_statement)

            if word_count < min_words:
                logger.warning(f"Low word count ({word_count} < {min_words}): {filepath.name}")
                return ExtractionResult(
                    success=False,
                    text=text,
                    word_count=word_count,
                    error=f"Insufficient text: {word_count} < {min_words} words"
                )

            logger.info(f"✓ Extracted {word_count} words from {filepath.name}")

            return ExtractionResult(
                success=True,
                text=text,
                word_count=word_count,
                format='html',
                metadata={'filepath': str(filepath)}
            )

        except Exception as e:
            logger.error(f"Extraction failed for {filepath}: {e}")
            return ExtractionResult(
                success=False,
                error=str(e)
            )

    def extract_pdf(self, filepath: Path) -> ExtractionResult:
        """
        Extract text from PDF document.

        Algorithm (from Document 01, Section 2.2):
        1. Open PDF with pdfplumber
        2. Extract text from each page
        3. Join pages with double newline
        4. Clean whitespace

        Args:
            filepath: Path to PDF file

        Returns:
            ExtractionResult with extracted text
        """
        try:
            with pdfplumber.open(filepath) as pdf:
                text_parts = []

                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                # Join pages
                text = '\n\n'.join(text_parts)

                # Clean whitespace
                text = self._clean_text(text)

                # Calculate word count
                word_count = len(text.split())

                logger.info(f"✓ Extracted {word_count} words from {filepath.name} "
                           f"({len(pdf.pages)} pages)")

                return ExtractionResult(
                    success=True,
                    text=text,
                    word_count=word_count,
                    format='pdf',
                    metadata={'filepath': str(filepath), 'num_pages': len(pdf.pages)}
                )

        except Exception as e:
            logger.error(f"PDF extraction failed for {filepath}: {e}")
            return ExtractionResult(
                success=False,
                error=str(e)
            )

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Normalization (from Document 01):
        - Replace multiple newlines with double newline
        - Replace multiple spaces with single space
        - Strip leading/trailing whitespace
        """
        # Normalize newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Collapse excessive blank lines

        # Normalize spaces
        text = re.sub(r' +', ' ', text)  # Collapse multiple spaces

        # Strip whitespace
        text = text.strip()

        return text

    def _remove_boilerplate(self, text: str) -> str:
        """
        Remove Fed boilerplate text.

        Common patterns identified in Document 01:
        - "Board of Governors of the Federal Reserve System"
        - "For media inquiries, call..."
        - "Last Update: ..."
        - Navigation breadcrumbs
        """
        # Remove standard disclaimers
        patterns = [
            r'Board of Governors of the Federal Reserve System',
            r'For media inquiries, call \d{3}-\d{3}-\d{4}',
            r'Last [Uu]pdate:.*\d{4}',
            r'Home\s*>\s*Monetary Policy',
            r'Share on (Twitter|Facebook|LinkedIn)',
            r'Accessibility\s*\|?\s*Contact',
            r'Federal Reserve Board - FOMC',
        ]

        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Clean up resulting whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        return text.strip()


# Example usage
if __name__ == '__main__':
    import yaml

    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    extractor = TextExtractor(config)

    # Test extraction on a sample file
    filepath = Path('data/raw/policy_statement_20211215.html')
    if filepath.exists():
        result = extractor.extract(filepath, 'policy_statement')

        if result.success:
            print(f"✓ Extracted {result.word_count} words")
            print(f"First 200 chars:\n{result.text[:200]}...")
        else:
            print(f"✗ Failed: {result.error}")
