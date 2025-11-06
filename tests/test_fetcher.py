"""Unit tests for DocumentFetcher module."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

from fedspeak.fetcher import DocumentFetcher, DownloadResult


class TestDocumentFetcher:
    """Test suite for DocumentFetcher class."""

    def test_initialization(self, sample_config, temp_data_dir):
        """Test fetcher initializes correctly."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {
            'policy_statement': 'https://example.com/monetary{date}.htm'
        }
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.1,
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        fetcher = DocumentFetcher(config)

        assert fetcher.config == config
        assert fetcher.output_dir.exists()
        assert fetcher.delay == 0.1
        assert fetcher.max_retries == 3

    def test_construct_url(self, sample_config, temp_data_dir):
        """Test URL construction from templates."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {
            'policy_statement': 'https://www.federalreserve.gov/newsevents/pressreleases/monetary{date}.htm'
        }
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.1,
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        fetcher = DocumentFetcher(config)
        url = fetcher._construct_url('policy_statement', '20211215')

        assert url == 'https://www.federalreserve.gov/newsevents/pressreleases/monetary20211215.htm'

    def test_construct_url_invalid_type(self, sample_config, temp_data_dir):
        """Test URL construction with invalid document type."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {'policy_statement': 'https://example.com/{date}'}
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.1,
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        fetcher = DocumentFetcher(config)

        with pytest.raises(ValueError, match="Unknown document type"):
            fetcher._construct_url('invalid_type', '20211215')

    @patch('fedspeak.fetcher.requests.Session')
    def test_download_document_success(self, mock_session, sample_config, temp_data_dir, mock_response_success):
        """Test successful document download."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {'policy_statement': 'https://example.com/monetary{date}.htm'}
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.01,  # Fast for testing
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        # Mock session.get to return success
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response_success
        mock_session.return_value = mock_session_instance

        fetcher = DocumentFetcher(config)
        fetcher.session = mock_session_instance

        result = fetcher.download_document('policy_statement', '20211215')

        assert result.success is True
        assert result.doc_type == 'policy_statement'
        assert result.date == '20211215'
        assert result.filepath is not None
        assert result.file_size > 0
        assert result.error is None

    @patch('fedspeak.fetcher.requests.Session')
    def test_download_document_404(self, mock_session, sample_config, temp_data_dir, mock_response_404):
        """Test document download with 404 response."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {'policy_statement': 'https://example.com/monetary{date}.htm'}
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.01,
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response_404
        mock_session.return_value = mock_session_instance

        fetcher = DocumentFetcher(config)
        fetcher.session = mock_session_instance

        result = fetcher.download_document('policy_statement', '20070101')

        assert result.success is False
        assert result.error == "404 Not Found - document may not exist"
        assert result.filepath is None

    def test_generate_fomc_dates(self, sample_config, temp_data_dir):
        """Test FOMC date generation."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {'policy_statement': 'https://example.com/{date}'}
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.1,
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        fetcher = DocumentFetcher(config)

        start = datetime(2021, 1, 1)
        end = datetime(2021, 12, 31)

        dates = fetcher._generate_fomc_dates(start, end)

        # Should generate ~8-9 dates (every 6 weeks for a year)
        assert len(dates) >= 7
        assert len(dates) <= 10
        assert all(isinstance(d, str) for d in dates)
        assert all(len(d) == 8 for d in dates)  # YYYYMMDD format

    def test_save_metadata(self, sample_config, temp_data_dir):
        """Test metadata saving."""
        config = sample_config
        config['corpus'] = {
            'data_dir': str(temp_data_dir / 'data'),
            'raw_subdir': 'raw',
            'metadata_subdir': 'metadata'
        }
        config['url_templates'] = {'policy_statement': 'https://example.com/{date}'}
        config['download'] = {
            'user_agent': 'Test Agent',
            'delay_seconds': 0.1,
            'retry_attempts': 3,
            'timeout_seconds': 10,
            'backoff_base': 1
        }

        fetcher = DocumentFetcher(config)

        result = DownloadResult(
            success=True,
            doc_type='policy_statement',
            date='20211215',
            filepath=Path('/test/path.html'),
            file_size=1234,
            url='https://example.com/test',
            timestamp=datetime.now()
        )

        fetcher._save_metadata(result)

        # Check metadata file was created
        metadata_file = temp_data_dir / 'data' / 'metadata' / 'download_log.json'
        assert metadata_file.exists()

        # Verify content
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        assert len(metadata) == 1
        assert metadata[0]['doc_type'] == 'policy_statement'
        assert metadata[0]['date'] == '20211215'
        assert metadata[0]['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
