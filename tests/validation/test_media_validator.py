"""Tests for Media Validator (Phase 6)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.validation.media_validator import MediaValidator


class TestMediaValidator:
    """Test cases for Media Validator."""

    @patch('src.validation.media_validator.HybridSentimentScorer')
    @patch('src.validation.media_validator.GDELTClient')
    def test_initialization(self, mock_gdelt, mock_sentiment):
        """Test media validator initialization."""
        validator = MediaValidator()

        assert validator.enabled is True
        assert validator.coverage_threshold == 50
        assert validator.diversity_threshold == 15
        assert validator.sentiment_threshold == 0.3

    @patch('src.validation.media_validator.HybridSentimentScorer')
    @patch('src.validation.media_validator.GDELTClient')
    def test_empty_result(self, mock_gdelt, mock_sentiment):
        """Test _empty_result method."""
        validator = MediaValidator()

        result = validator._empty_result(error="Test error")

        assert result['validated'] is False
        assert result['media_score'] == 0.0
        assert result['error'] == "Test error"

    @patch('src.validation.media_validator.HybridSentimentScorer')
    @patch('src.validation.media_validator.GDELTClient')
    def test_sentiment_label(self, mock_gdelt, mock_sentiment):
        """Test sentiment score to label conversion."""
        validator = MediaValidator()

        assert validator._sentiment_label(0.5) == 'positive'
        assert validator._sentiment_label(0.05) == 'neutral'
        assert validator._sentiment_label(-0.5) == 'negative'

    @patch('src.validation.media_validator.HybridSentimentScorer')
    @patch('src.validation.media_validator.GDELTClient')
    @patch('src.validation.media_validator.MediaDataCache')
    def test_validate_shift_high_coverage(self, mock_cache, mock_gdelt_cls, mock_sentiment):
        """Test validation with high media coverage."""
        # Setup mocks
        mock_gdelt = mock_gdelt_cls.return_value
        mock_cache_inst = mock_cache.return_value

        # Mock GDELT search results (high coverage)
        mock_articles = [
            {'domain': f'source{i}.com', 'tone': -5.0, 'title': f'Article {i}'}
            for i in range(60)  # 60 articles (above threshold of 50)
        ]

        mock_gdelt.search_fomc_coverage.return_value = mock_articles
        mock_gdelt.calculate_coverage_metrics.return_value = {
            'total_articles': 60,
            'unique_sources': 20,  # Above threshold of 15
            'priority_sources_list': ['reuters.com', 'bloomberg.com']
        }
        mock_gdelt.get_top_articles.return_value = mock_articles[:20]

        # Mock sentiment analysis
        mock_sentiment_inst = mock_sentiment.return_value
        mock_sentiment_inst.score_articles.return_value = {
            'gdelt_tone_avg': -5.0,
            'finbert_sentiment_avg': -0.6,
            'hybrid_score': -0.5,  # Above threshold of 0.3 (absolute)
            'article_count': 20
        }

        # Mock cache misses
        mock_cache_inst.get_gdelt_cache.return_value = None
        mock_cache_inst.get_sentiment_cache.return_value = None

        # Create validator
        validator = MediaValidator(
            gdelt_client=mock_gdelt,
            sentiment_scorer=mock_sentiment_inst,
            cache=mock_cache_inst
        )

        # Run validation
        result = validator.validate_shift(
            date="20211215",
            term="transitory",
            shift_type="removal"
        )

        # Assertions
        assert result['validated'] is True  # All 3 indicators triggered
        assert result['coverage_volume'] == 60
        assert result['source_diversity'] == 20
        assert result['signals']['coverage_volume'] == 1
        assert result['signals']['source_diversity'] == 1
        assert result['signals']['sentiment_significance'] == 1
        assert result['media_score'] >= 0.6  # Should meet threshold

    @patch('src.validation.media_validator.HybridSentimentScorer')
    @patch('src.validation.media_validator.GDELTClient')
    @patch('src.validation.media_validator.MediaDataCache')
    def test_validate_shift_low_coverage(self, mock_cache, mock_gdelt_cls, mock_sentiment):
        """Test validation with low media coverage."""
        mock_gdelt = mock_gdelt_cls.return_value
        mock_cache_inst = mock_cache.return_value

        # Mock GDELT search results (low coverage)
        mock_articles = [
            {'domain': f'source{i}.com', 'tone': -2.0, 'title': f'Article {i}'}
            for i in range(10)  # Only 10 articles (below threshold)
        ]

        mock_gdelt.search_fomc_coverage.return_value = mock_articles
        mock_gdelt.calculate_coverage_metrics.return_value = {
            'total_articles': 10,
            'unique_sources': 5,  # Below threshold
            'priority_sources_list': []
        }
        mock_gdelt.get_top_articles.return_value = mock_articles

        # Mock sentiment
        mock_sentiment_inst = mock_sentiment.return_value
        mock_sentiment_inst.score_articles.return_value = {
            'gdelt_tone_avg': -2.0,
            'finbert_sentiment_avg': -0.1,
            'hybrid_score': -0.12,  # Below threshold
            'article_count': 10
        }

        # Mock cache misses
        mock_cache_inst.get_gdelt_cache.return_value = None
        mock_cache_inst.get_sentiment_cache.return_value = None

        validator = MediaValidator(
            gdelt_client=mock_gdelt,
            sentiment_scorer=mock_sentiment_inst,
            cache=mock_cache_inst
        )

        result = validator.validate_shift(
            date="20211215",
            term="transitory",
            shift_type="removal"
        )

        # Should not validate (no indicators triggered)
        assert result['validated'] is False
        assert result['coverage_volume'] == 10
        assert result['signals']['coverage_volume'] == 0  # Below threshold
        assert result['signals']['source_diversity'] == 0
        assert result['media_score'] < 0.6
