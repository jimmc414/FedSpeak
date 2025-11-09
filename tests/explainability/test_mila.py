"""Tests for MILA stance analyzer and supporting modules.

Note: These tests use mocked Anthropic API responses.
To run tests with real API (requires ANTHROPIC_API_KEY):
    pytest tests/explainability/test_mila.py --real-api
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.explainability import MILAAnalyzer, MILAStanceCache, CostTracker


class TestMILAAnalyzer:
    """Test cases for MILA stance analyzer."""

    @pytest.fixture
    def mock_anthropic_response(self):
        """Mock Anthropic API response."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            'stance': 'hawkish',
            'score': 0.75,
            'confidence': 0.90,
            'explanation': 'The statement signals tightening policy with emphasis on inflation control.',
            'key_phrases': ['reduce inflation', 'raise rates', 'price stability']
        })
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 150
        return mock_response

    @patch('anthropic.Anthropic')
    def test_initialization_with_api_key(self, mock_anthropic):
        """Test MILA initializes with API key."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = MILAAnalyzer(api_key='test-key')
            assert analyzer.is_enabled()

    def test_initialization_without_api_key(self):
        """Test MILA gracefully handles missing API key."""
        # Reset singleton
        MILAAnalyzer._instance = None
        MILAAnalyzer._client = None

        with patch.dict('os.environ', {}, clear=True):
            with patch('src.explainability.mila_analyzer.Settings') as mock_settings:
                mock_settings.return_value.get.return_value = None
                analyzer = MILAAnalyzer()
                assert not analyzer.is_enabled()

    @patch('anthropic.Anthropic')
    def test_analyze_stance_success(self, mock_anthropic, mock_anthropic_response):
        """Test stance analysis with mocked API."""
        # Reset singleton
        MILAAnalyzer._instance = None
        MILAAnalyzer._client = None

        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.return_value = mock_client

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            # Mock cost tracker to avoid Decimal issues
            with patch('src.explainability.cost_tracker.CostTracker'):
                analyzer = MILAAnalyzer(api_key='test-key')
                result = analyzer.analyze_stance('Test statement text', '20211215')

                assert result['success'] is True
                assert result['stance'] == 'hawkish'
                assert result['score'] == 0.75
                assert result['confidence'] == 0.90
                assert len(result['key_phrases']) == 3

    @patch('anthropic.Anthropic')
    def test_analyze_stance_caching(self, mock_anthropic, mock_anthropic_response, tmp_path):
        """Test that results are cached."""
        # Reset singleton
        MILAAnalyzer._instance = None
        MILAAnalyzer._client = None
        MILAAnalyzer._cache = None

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.return_value = mock_client

        # Use temporary cache directory to avoid persistence between tests
        temp_cache = tmp_path / "test_cache"

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('src.explainability.cost_tracker.CostTracker'):
                analyzer = MILAAnalyzer(api_key='test-key', cache_dir=str(temp_cache))

                # First call - should hit API
                result1 = analyzer.analyze_stance('Test statement', '20211299')  # Unique date
                assert result1['cached'] is False

                # Second call - should use cache
                result2 = analyzer.analyze_stance('Test statement', '20211299')
                assert result2['cached'] is True

                # API should only be called once
                assert mock_client.messages.create.call_count == 1

    def test_analyze_stance_without_api_key(self):
        """Test stance analysis fails gracefully without API key."""
        # Reset singleton
        MILAAnalyzer._instance = None
        MILAAnalyzer._client = None

        with patch.dict('os.environ', {}, clear=True):
            with patch('src.explainability.mila_analyzer.Settings') as mock_settings:
                mock_settings.return_value.get.return_value = None
                analyzer = MILAAnalyzer()
                result = analyzer.analyze_stance('Test', '20211215')

                assert result['success'] is False
                assert result['error'] == 'MILA_DISABLED'


class TestMILAStanceCache:
    """Test cases for MILA cache."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / 'test_mila_cache'
        return str(cache_dir)

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initializes correctly."""
        cache = MILAStanceCache(cache_dir=temp_cache_dir)
        assert cache.stance_dir.exists()

    def test_cache_save_and_retrieve(self, temp_cache_dir):
        """Test saving and retrieving cached stance."""
        cache = MILAStanceCache(cache_dir=temp_cache_dir)

        # Save stance
        test_result = {
            'stance': 'dovish',
            'score': -0.60,
            'confidence': 0.85,
            'explanation': 'Test explanation',
            'key_phrases': ['test phrase']
        }

        cache.save_stance('20211215', 'policy_statement', test_result)

        # Retrieve stance
        retrieved = cache.get_stance('20211215', 'policy_statement')

        assert retrieved is not None
        assert retrieved['stance'] == 'dovish'
        assert retrieved['score'] == -0.60
        assert retrieved['confidence'] == 0.85

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss returns None."""
        cache = MILAStanceCache(cache_dir=temp_cache_dir)
        result = cache.get_stance('20999999', 'policy_statement')
        assert result is None

    def test_cache_stats(self, temp_cache_dir):
        """Test cache statistics."""
        cache = MILAStanceCache(cache_dir=temp_cache_dir)

        # Save some entries
        for i in range(3):
            cache.save_stance(f'2021121{i}', 'policy_statement', {
                'stance': 'neutral',
                'score': 0.0,
                'confidence': 0.5,
                'explanation': 'Test',
                'key_phrases': []
            })

        stats = cache.get_stats()
        assert stats['cache_files'] >= 3
        assert stats['cache_size_mb'] >= 0  # Can be 0 for very small files


class TestCostTracker:
    """Test cases for cost tracker."""

    @pytest.fixture
    def temp_storage_file(self, tmp_path):
        """Create temporary storage file."""
        storage_file = tmp_path / 'test_cost_tracking.json'
        return str(storage_file)

    def test_cost_tracker_initialization(self, temp_storage_file):
        """Test cost tracker initializes."""
        tracker = CostTracker(storage_file=temp_storage_file)
        assert tracker.data['total_requests'] == 0
        assert tracker.data['total_cost'] == 0.0

    def test_track_request(self, temp_storage_file):
        """Test tracking a single request."""
        tracker = CostTracker(storage_file=temp_storage_file)

        cost = tracker.track_request(
            input_tokens=500,
            output_tokens=150,
            model='claude-3-5-sonnet-20241022'
        )

        assert cost > 0
        assert tracker.data['total_requests'] == 1
        assert tracker.data['total_input_tokens'] == 500
        assert tracker.data['total_output_tokens'] == 150

    def test_cost_calculation(self, temp_storage_file):
        """Test cost calculation accuracy."""
        tracker = CostTracker(storage_file=temp_storage_file)

        # Claude Sonnet: $3/M input, $15/M output
        # 1000 input + 1000 output = $0.018
        cost = tracker.track_request(
            input_tokens=1000,
            output_tokens=1000,
            model='claude-3-5-sonnet-20241022'
        )

        expected_cost = (1000/1_000_000 * 3.0) + (1000/1_000_000 * 15.0)
        assert abs(cost - expected_cost) < 0.001

    def test_get_summary(self, temp_storage_file):
        """Test cost summary."""
        tracker = CostTracker(storage_file=temp_storage_file)

        # Track some requests
        for _ in range(5):
            tracker.track_request(100, 50, 'claude-3-5-sonnet-20241022')

        summary = tracker.get_summary()
        assert summary['total_requests'] == 5
        assert summary['total_cost'] > 0
        assert 'average_cost_per_request' in summary
