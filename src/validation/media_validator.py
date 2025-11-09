"""Media coverage validator for FedSpeak language shift detection.

This module validates detected language shifts by analyzing media coverage
using GDELT news data and FinBERT sentiment analysis.

Validation Indicators:
1. Coverage Volume: Number of articles mentioning the term
2. Source Diversity: Number of unique news sources
3. Sentiment Significance: Absolute average sentiment score

Multi-signal approach combines statistical detection with external media
validation to reduce false positives and improve precision.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config.settings import get_settings
from src.external.gdelt_client import GDELTClient
from src.external.media_cache import MediaDataCache
from src.validation.sentiment_analyzer import HybridSentimentScorer

logger = logging.getLogger(__name__)


class MediaValidator:
    """Media coverage validator for FOMC language shifts.

    Validates detected language shifts by analyzing media coverage patterns:
    - How many articles mention the term?
    - How many unique sources cover it?
    - What is the sentiment tone of coverage?

    Uses GDELT Project for news data and FinBERT for sentiment analysis.
    Implements caching to avoid redundant API calls and computation.
    """

    def __init__(self,
                 gdelt_client: Optional[GDELTClient] = None,
                 sentiment_scorer: Optional[HybridSentimentScorer] = None,
                 cache: Optional[MediaDataCache] = None,
                 config: Optional[Dict] = None):
        """Initialize media validator.

        Args:
            gdelt_client: GDELT API client (creates new if None)
            sentiment_scorer: Hybrid sentiment scorer (creates new if None)
            cache: Media data cache (creates new if None)
            config: Configuration dict (loads from settings if None)

        Raises:
            RuntimeError: If FinBERT model fails to load
        """
        self.config = config or get_settings()

        # Load configuration
        media_config = self.config.get('media_validation', {})

        self.enabled = media_config.get('enabled', True)

        # Initialize components
        self.gdelt = gdelt_client or GDELTClient(
            timeout=media_config.get('apis', {}).get('gdelt', {}).get('timeout', 30)
        )

        cache_dir = media_config.get('storage', {}).get('cache_dir', 'data/media_cache')
        retention_days = media_config.get('storage', {}).get('retention_days', 90)
        self.cache = cache or MediaDataCache(cache_dir, retention_days)

        # Initialize sentiment analyzer (may take time to load FinBERT model)
        try:
            sentiment_config = media_config.get('sentiment', {})
            top_n = sentiment_config.get('top_n_articles', 20)

            self.sentiment = sentiment_scorer or HybridSentimentScorer(
                gdelt_weight=0.4,
                finbert_weight=0.6
            )

            self.top_n_articles = top_n

        except Exception as e:
            logger.error(f"Failed to initialize FinBERT: {e}")
            logger.warning("Media validation disabled due to sentiment analyzer failure")
            self.enabled = False
            raise RuntimeError(f"FinBERT initialization failed: {e}")

        # Load indicator thresholds
        indicators = media_config.get('indicators', {})

        self.coverage_threshold = indicators.get('coverage_volume', {}).get('threshold_articles', 50)
        self.coverage_weight = indicators.get('coverage_volume', {}).get('weight', 0.35)

        self.diversity_threshold = indicators.get('source_diversity', {}).get('threshold_sources', 15)
        self.diversity_weight = indicators.get('source_diversity', {}).get('weight', 0.35)

        self.sentiment_threshold = indicators.get('sentiment_significance', {}).get('threshold_abs_score', 0.3)
        self.sentiment_weight = indicators.get('sentiment_significance', {}).get('weight', 0.30)

        # Load validation criteria
        validation = media_config.get('validation', {})
        self.min_score = validation.get('min_score', 0.6)
        self.min_indicators = validation.get('min_indicators', 2)

        # Search window
        self.search_window_hours = media_config.get('apis', {}).get('gdelt', {}).get('search_window_hours', 24)

        logger.info(
            f"Media validator initialized (enabled={self.enabled}, "
            f"thresholds: coverage={self.coverage_threshold}, "
            f"diversity={self.diversity_threshold}, "
            f"sentiment={self.sentiment_threshold})"
        )

    def validate_shift(self, date: str, term: str, shift_type: str) -> Dict:
        """Validate a detected language shift using media coverage analysis.

        Args:
            date: FOMC statement date (YYYYMMDD)
            term: Term that shifted
            shift_type: Type of shift (emergence/removal/increase/decrease)

        Returns:
            Dictionary with validation results:
            - validated: Boolean (True if media confirms shift)
            - media_score: Weighted score (0-1 scale)
            - coverage_volume: Number of articles
            - source_diversity: Number of unique sources
            - gdelt_tone_avg: Average GDELT tone score
            - finbert_sentiment_avg: Average FinBERT sentiment
            - hybrid_sentiment: Combined sentiment score
            - signals: Dict of indicator triggers (0 or 1)
            - timestamp: Validation timestamp
            - error: Error message (None if success)
        """
        if not self.enabled:
            logger.warning("Media validation disabled")
            return self._empty_result(error="Media validation disabled")

        logger.info(f"Validating shift: date={date}, term='{term}', type={shift_type}")

        try:
            # Check cache first
            cached_articles = self.cache.get_gdelt_cache(date, term)

            if cached_articles is not None:
                logger.info(f"Using cached GDELT data for {date}_{term}")
                articles = cached_articles
            else:
                # Fetch from GDELT
                articles = self.gdelt.search_fomc_coverage(
                    term=term,
                    fomc_date=date,
                    window_hours=self.search_window_hours
                )

                # Cache results
                self.cache.save_gdelt_cache(date, term, articles)

            if not articles:
                logger.warning(f"No media coverage found for {term} on {date}")
                return self._empty_result(
                    error=f"No media coverage found (term={term}, date={date})"
                )

            # Calculate coverage metrics
            metrics = self.gdelt.calculate_coverage_metrics(articles)

            coverage_volume = metrics['total_articles']
            source_diversity = metrics['unique_sources']

            # Check sentiment cache
            cached_sentiment = self.cache.get_sentiment_cache(date, term)

            if cached_sentiment is not None:
                logger.info(f"Using cached sentiment data for {date}_{term}")
                sentiment_data = cached_sentiment.get('results', {})
            else:
                # Get top articles for sentiment analysis
                top_articles = self.gdelt.get_top_articles(articles, n=self.top_n_articles)

                # Analyze sentiment (hybrid GDELT + FinBERT)
                sentiment_data = self.sentiment.score_articles(top_articles)

                # Cache sentiment results
                self.cache.save_sentiment_cache(date, term, sentiment_data)

            gdelt_tone = sentiment_data.get('gdelt_tone_avg', 0.0)
            finbert_sentiment = sentiment_data.get('finbert_sentiment_avg', 0.0)
            hybrid_sentiment = sentiment_data.get('hybrid_score', 0.0)

            # Calculate signals (binary: 1 if threshold met, 0 otherwise)
            signals = {
                'coverage_volume': 1 if coverage_volume >= self.coverage_threshold else 0,
                'source_diversity': 1 if source_diversity >= self.diversity_threshold else 0,
                'sentiment_significance': 1 if abs(hybrid_sentiment) >= self.sentiment_threshold else 0
            }

            # Calculate weighted media score
            media_score = (
                signals['coverage_volume'] * self.coverage_weight +
                signals['source_diversity'] * self.diversity_weight +
                signals['sentiment_significance'] * self.sentiment_weight
            )

            indicators_triggered = sum(signals.values())

            # Determine validation
            validated = (
                media_score >= self.min_score and
                indicators_triggered >= self.min_indicators
            )

            logger.info(
                f"Media validation result: validated={validated}, "
                f"score={media_score:.2f}, indicators={indicators_triggered}/3"
            )

            return {
                'validated': validated,
                'media_score': round(media_score, 4),
                'coverage_volume': coverage_volume,
                'source_diversity': source_diversity,
                'gdelt_tone_avg': round(gdelt_tone, 2),
                'finbert_sentiment_avg': round(finbert_sentiment, 4),
                'hybrid_sentiment': round(hybrid_sentiment, 4),
                'sentiment_label': self._sentiment_label(hybrid_sentiment),
                'top_sources': metrics.get('priority_sources_list', [])[:5],
                'signals': signals,
                'indicators_triggered': indicators_triggered,
                'timestamp': datetime.now().isoformat(),
                'error': None
            }

        except Exception as e:
            logger.error(f"Media validation failed: {e}")
            return self._empty_result(error=str(e))

    def get_validation_summary(self, validation_result: Dict) -> str:
        """Generate human-readable validation summary.

        Args:
            validation_result: Result dictionary from validate_shift()

        Returns:
            Multi-line summary string
        """
        if validation_result.get('error'):
            return f"Media Validation: ERROR - {validation_result['error']}"

        validated = validation_result.get('validated', False)
        score = validation_result.get('media_score', 0.0)
        indicators = validation_result.get('indicators_triggered', 0)

        status = "VALIDATED" if validated else "NOT VALIDATED"

        summary = [
            f"Media Validation: {status}",
            f"  Score: {score:.2f} (threshold: {self.min_score})",
            f"  Indicators: {indicators}/3 (minimum: {self.min_indicators})",
            "",
            "  Coverage Metrics:",
            f"    Articles: {validation_result.get('coverage_volume', 0)} (threshold: {self.coverage_threshold})",
            f"    Sources: {validation_result.get('source_diversity', 0)} (threshold: {self.diversity_threshold})",
            f"    Sentiment: {validation_result.get('hybrid_sentiment', 0.0):.2f} (threshold: ±{self.sentiment_threshold})",
            "",
            f"  Sentiment Analysis:",
            f"    GDELT Tone: {validation_result.get('gdelt_tone_avg', 0.0)}",
            f"    FinBERT: {validation_result.get('finbert_sentiment_avg', 0.0):.2f}",
            f"    Hybrid: {validation_result.get('hybrid_sentiment', 0.0):.2f} ({validation_result.get('sentiment_label', 'neutral')})"
        ]

        top_sources = validation_result.get('top_sources', [])
        if top_sources:
            summary.append("")
            summary.append(f"  Top Sources: {', '.join(top_sources[:5])}")

        return "\n".join(summary)

    def _empty_result(self, error: Optional[str] = None) -> Dict:
        """Create empty validation result (for errors or no data).

        Args:
            error: Optional error message

        Returns:
            Empty validation result dictionary
        """
        return {
            'validated': False,
            'media_score': 0.0,
            'coverage_volume': 0,
            'source_diversity': 0,
            'gdelt_tone_avg': 0.0,
            'finbert_sentiment_avg': 0.0,
            'hybrid_sentiment': 0.0,
            'sentiment_label': 'neutral',
            'top_sources': [],
            'signals': {
                'coverage_volume': 0,
                'source_diversity': 0,
                'sentiment_significance': 0
            },
            'indicators_triggered': 0,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }

    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to human-readable label.

        Args:
            score: Sentiment score (-1 to +1)

        Returns:
            Label: 'positive', 'neutral', or 'negative'
        """
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
