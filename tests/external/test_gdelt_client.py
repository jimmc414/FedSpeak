"""Tests for GDELT API client (Phase 6)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.external.gdelt_client import GDELTClient


class TestGDELTClient:
    """Test cases for GDELT client."""

    def test_initialization(self):
        """Test GDELT client initialization."""
        client = GDELTClient(timeout=30)

        assert client.timeout == 30
        assert client.rate_limit is None  # Default: unlimited
        assert client.API_BASE_URL == "https://api.gdeltproject.org/api/v2/doc/doc"

    def test_date_parsing_yyyymmdd(self):
        """Test date parsing for YYYYMMDD format."""
        client = GDELTClient()

        dt = client._parse_date("20211215")

        assert dt.year == 2021
        assert dt.month == 12
        assert dt.day == 15

    def test_date_parsing_yyyymmddhhmmss(self):
        """Test date parsing for YYYYMMDDHHMMSS format."""
        client = GDELTClient()

        dt = client._parse_date("20211215140000")

        assert dt.year == 2021
        assert dt.month == 12
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 0

    def test_calculate_coverage_metrics_empty(self):
        """Test coverage metrics with empty article list."""
        client = GDELTClient()

        metrics = client.calculate_coverage_metrics([])

        assert metrics['total_articles'] == 0
        assert metrics['unique_sources'] == 0
        assert metrics['avg_tone'] == 0.0

    def test_calculate_coverage_metrics(self):
        """Test coverage metrics calculation."""
        client = GDELTClient()

        articles = [
            {'domain': 'reuters.com', 'tone': '-5.5'},
            {'domain': 'bloomberg.com', 'tone': '-3.2'},
            {'domain': 'reuters.com', 'tone': '-4.1'}
        ]

        metrics = client.calculate_coverage_metrics(articles)

        assert metrics['total_articles'] == 3
        assert metrics['unique_sources'] == 2
        assert 'reuters.com' in metrics['sources_list']
        assert 'bloomberg.com' in metrics['sources_list']
        # Average tone: (-5.5 + -3.2 + -4.1) / 3 = -4.27
        assert metrics['avg_tone'] == pytest.approx(-4.27, abs=0.01)

    def test_filter_priority_sources(self):
        """Test filtering to priority sources only."""
        client = GDELTClient()

        articles = [
            {'domain': 'reuters.com', 'title': 'Article 1'},
            {'domain': 'example.com', 'title': 'Article 2'},
            {'domain': 'bloomberg.com', 'title': 'Article 3'}
        ]

        filtered = client.filter_priority_sources(articles)

        assert len(filtered) == 2  # Only reuters and bloomberg
        assert filtered[0]['domain'] == 'reuters.com'
        assert filtered[1]['domain'] == 'bloomberg.com'

    def test_get_top_articles(self):
        """Test getting top articles by relevance."""
        client = GDELTClient()

        articles = [
            {'domain': 'reuters.com', 'tone': '-10.0', 'title': 'High priority'},
            {'domain': 'example.com', 'tone': '-2.0', 'title': 'Low priority'},
            {'domain': 'bloomberg.com', 'tone': '-8.0', 'title': 'Medium priority'}
        ]

        top = client.get_top_articles(articles, n=2)

        assert len(top) == 2
        # Reuters should be first (priority source + high tone)
        assert top[0]['domain'] == 'reuters.com'
        # Bloomberg should be second
        assert top[1]['domain'] == 'bloomberg.com'

    @patch('src.external.gdelt_client.requests.get')
    def test_search_success(self, mock_get):
        """Test successful GDELT search."""
        client = GDELTClient()

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'articles': [
                {
                    'url': 'https://reuters.com/article1',
                    'title': 'FOMC drops transitory',
                    'domain': 'reuters.com',
                    'tone': '-5.5'
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        results = client.search(
            query="FOMC AND transitory",
            start_date="20211215"
        )

        assert len(results) == 1
        assert results[0]['title'] == 'FOMC drops transitory'
        assert results[0]['domain'] == 'reuters.com'

    @patch('src.external.gdelt_client.requests.get')
    def test_search_timeout(self, mock_get):
        """Test GDELT search timeout handling."""
        import requests
        client = GDELTClient(timeout=1)

        mock_get.side_effect = requests.Timeout("Request timeout")

        with pytest.raises(requests.Timeout):
            client.search(query="FOMC", start_date="20211215")

    @patch('src.external.gdelt_client.requests.get')
    def test_search_api_error(self, mock_get):
        """Test GDELT API error handling."""
        import requests
        client = GDELTClient()

        mock_get.side_effect = requests.RequestException("API error")

        with pytest.raises(requests.RequestException):
            client.search(query="FOMC", start_date="20211215")
