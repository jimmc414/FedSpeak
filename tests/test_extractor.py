"""Unit tests for TextExtractor module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from fedspeak.extractor import TextExtractor, ExtractionResult


class TestTextExtractor:
    """Test suite for TextExtractor class."""

    def test_initialization_default(self):
        """Test extractor initializes with defaults."""
        extractor = TextExtractor()

        assert extractor.min_word_count_statement == 100
        assert extractor.min_word_count_minutes == 1000

    def test_initialization_custom_config(self):
        """Test extractor initializes with custom config."""
        config = {
            'validation': {
                'min_word_count_statement': 200,
                'min_word_count_minutes': 1500
            }
        }

        extractor = TextExtractor(config)

        assert extractor.min_word_count_statement == 200
        assert extractor.min_word_count_minutes == 1500

    def test_extract_html_modern_format(self, sample_html_2021, temp_data_dir):
        """Test extraction from modern HTML format (2013+)."""
        # Create test file
        test_file = temp_data_dir / "test_2021.html"
        test_file.write_text(sample_html_2021)

        extractor = TextExtractor({'validation': {'min_word_count_statement': 10}})
        result = extractor.extract(test_file, 'policy_statement')

        assert result.success is True
        assert result.word_count > 10
        assert "full range of tools" in result.text
        assert result.format == 'html'
        assert result.error is None

    def test_extract_html_legacy_format(self, sample_html_2010, temp_data_dir):
        """Test extraction from legacy HTML format (2008-2012)."""
        # Create test file
        test_file = temp_data_dir / "test_2010.html"
        test_file.write_text(sample_html_2010)

        extractor = TextExtractor({'validation': {'min_word_count_statement': 10}})
        result = extractor.extract(test_file, 'policy_statement')

        assert result.success is True
        assert result.word_count > 10
        assert "Federal Open Market Committee" in result.text
        assert result.format == 'html'

    def test_extract_file_not_found(self):
        """Test extraction with non-existent file."""
        extractor = TextExtractor()
        result = extractor.extract(Path('/nonexistent/file.html'), 'policy_statement')

        assert result.success is False
        assert "File not found" in result.error

    def test_extract_insufficient_words(self, temp_data_dir):
        """Test extraction fails with insufficient word count."""
        # Create file with very little content
        short_html = """
        <html><body><div id="article">
        <p>Too short.</p>
        </div></body></html>
        """
        test_file = temp_data_dir / "short.html"
        test_file.write_text(short_html)

        extractor = TextExtractor({'validation': {'min_word_count_statement': 100}})
        result = extractor.extract(test_file, 'policy_statement')

        assert result.success is False
        assert "Insufficient text" in result.error
        assert result.word_count < 100

    def test_clean_text(self):
        """Test text cleaning function."""
        extractor = TextExtractor()

        # Test with excessive whitespace
        dirty_text = "This  is   text\n\n\n\nwith   spaces\n\n\n\nand\n\nnewlines"
        cleaned = extractor._clean_text(dirty_text)

        assert "  " not in cleaned  # No double spaces
        assert "\n\n\n" not in cleaned  # No triple newlines
        assert cleaned.startswith("This is")

    def test_remove_boilerplate(self):
        """Test boilerplate removal."""
        extractor = TextExtractor()

        text_with_boilerplate = """
        Board of Governors of the Federal Reserve System
        The Committee decided to maintain the target range.
        For media inquiries, call 202-452-2955
        Last Update: January 26, 2022
        """

        cleaned = extractor._remove_boilerplate(text_with_boilerplate)

        assert "Board of Governors" not in cleaned
        assert "For media inquiries" not in cleaned
        assert "Last Update" not in cleaned
        assert "maintain the target range" in cleaned

    def test_extract_html_cascading_selectors(self, temp_data_dir):
        """Test that cascading selectors work when article div is missing."""
        # HTML with no article div, but has body
        html_body_only = """
        <html>
        <body>
        <p>This is content in the body tag directly. The Federal Reserve decided
        to maintain the target range for the federal funds rate. This is a longer
        text to meet word count requirements for the test to pass successfully.</p>
        </body>
        </html>
        """
        test_file = temp_data_dir / "body_only.html"
        test_file.write_text(html_body_only)

        extractor = TextExtractor({'validation': {'min_word_count_statement': 10}})
        result = extractor.extract(test_file, 'policy_statement')

        assert result.success is True
        assert "Federal Reserve" in result.text

    def test_extract_html_removes_script_tags(self, temp_data_dir):
        """Test that script and style tags are removed."""
        html_with_scripts = """
        <html>
        <head><script>alert('test');</script></head>
        <body>
        <div id="article">
        <style>.test { color: red; }</style>
        <p>The Federal Reserve maintains its commitment to using all available
        tools to support the economy and promote maximum employment and price
        stability goals through appropriate monetary policy actions.</p>
        </div>
        </body>
        </html>
        """
        test_file = temp_data_dir / "with_scripts.html"
        test_file.write_text(html_with_scripts)

        extractor = TextExtractor({'validation': {'min_word_count_statement': 10}})
        result = extractor.extract(test_file, 'policy_statement')

        assert result.success is True
        assert "alert" not in result.text
        assert ".test" not in result.text
        assert "color: red" not in result.text
        assert "Federal Reserve" in result.text

    @patch('pdfplumber.open')
    def test_extract_pdf(self, mock_pdfplumber, temp_data_dir):
        """Test PDF extraction."""
        # Mock PDF object
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is page 1 content from a Federal Reserve document."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        test_file = temp_data_dir / "test.pdf"
        test_file.touch()  # Create empty file

        extractor = TextExtractor()
        result = extractor.extract_pdf(test_file)

        assert result.success is True
        assert result.format == 'pdf'
        assert "page 1 content" in result.text
        assert result.metadata['num_pages'] == 1

    @patch('pdfplumber.open')
    def test_extract_pdf_multiple_pages(self, mock_pdfplumber, temp_data_dir):
        """Test PDF extraction with multiple pages."""
        # Mock multiple pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "First page content."

        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Second page content."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        test_file = temp_data_dir / "multipage.pdf"
        test_file.touch()

        extractor = TextExtractor()
        result = extractor.extract_pdf(test_file)

        assert result.success is True
        assert "First page" in result.text
        assert "Second page" in result.text
        assert result.metadata['num_pages'] == 2

    @patch('pdfplumber.open')
    def test_extract_pdf_failure(self, mock_pdfplumber, temp_data_dir):
        """Test PDF extraction handles errors."""
        mock_pdfplumber.side_effect = Exception("PDF corrupted")

        test_file = temp_data_dir / "corrupted.pdf"
        test_file.touch()

        extractor = TextExtractor()
        result = extractor.extract_pdf(test_file)

        assert result.success is False
        assert "PDF corrupted" in result.error


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
