"""Tests for MarketValidator (Phase 5)."""

import pytest
from unittest.mock import Mock, patch
from src.validation.market_validator import MarketValidator


class TestMarketValidator:
    """Test cases for MarketValidator class."""

    def test_initialization_without_api_key(self):
        """Test that validator fails gracefully without FRED API key."""
        with patch('os.getenv', return_value=None):
            with pytest.raises(ValueError, match="FRED API key required"):
                from src.validation.fred_client import FREDClient
                FREDClient()

    def test_determine_tier_high_confidence_validated(self):
        """Test tier determination for high confidence + market validated + media validated (Phase 6)."""
        # Create validator with mocked clients
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                # Tier 1: Triple signal (statistical + market + media)
                tier_num, tier_name = validator.determine_tier('high', True, True)

                assert tier_num == 1
                assert tier_name == 'tier_1'

    def test_determine_tier_high_confidence_not_validated(self):
        """Test tier determination for high confidence + dual signal (Phase 6)."""
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                # Tier 2: Dual signal (statistical + market OR statistical + media)
                tier_num, tier_name = validator.determine_tier('high', True, False)

                assert tier_num == 2
                assert tier_name == 'tier_2'

    def test_determine_tier_low_confidence(self):
        """Test tier determination for low confidence (regardless of market)."""
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                tier_num, tier_name = validator.determine_tier('low', True)

                assert tier_num == 3
                assert tier_name == 'tier_3'

    def test_calculate_signals_all_triggered(self):
        """Test signal calculation when all thresholds exceeded."""
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                # Treasury changes above threshold (5 bps)
                # VIX above threshold (10%)
                # S&P500 above threshold (0.5%)
                signals = validator._calculate_signals(
                    dgs2_change=10.0,  # 10 bps > 5 bps threshold
                    dgs10_change=8.0,  # 8 bps > 5 bps threshold
                    vix_change=15.0,   # 15% > 10% threshold
                    sp500_change=1.0   # 1% > 0.5% threshold
                )

                assert signals['treasury_2yr'] == 1
                assert signals['treasury_10yr'] == 1
                assert signals['vix'] == 1
                assert signals['sp500'] == 1

    def test_calculate_signals_none_triggered(self):
        """Test signal calculation when no thresholds exceeded."""
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                signals = validator._calculate_signals(
                    dgs2_change=2.0,   # 2 bps < 5 bps threshold
                    dgs10_change=3.0,  # 3 bps < 5 bps threshold
                    vix_change=5.0,    # 5% < 10% threshold
                    sp500_change=0.2   # 0.2% < 0.5% threshold
                )

                assert signals['treasury_2yr'] == 0
                assert signals['treasury_10yr'] == 0
                assert signals['vix'] == 0
                assert signals['sp500'] == 0

    def test_calculate_market_score(self):
        """Test market score calculation with weighted signals."""
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                # 2 treasuries triggered (0.2 + 0.2 = 0.4)
                # VIX triggered (0.3)
                # S&P500 not triggered (0.0)
                # Total: 0.7
                signals = {
                    'treasury_2yr': 1,
                    'treasury_10yr': 1,
                    'vix': 1,
                    'sp500': 0
                }

                score = validator._calculate_market_score(signals)

                assert score == 0.7  # Should match weights

    def test_validation_summary(self):
        """Test human-readable validation summary generation."""
        with patch('src.validation.market_validator.FREDClient'):
            with patch('src.validation.market_validator.YahooClient'):
                validator = MarketValidator()

                validation_result = {
                    'validated': True,
                    'market_score': 0.75,
                    'indicators_triggered': 3,
                    'treasury_2yr_change': 10.5,
                    'treasury_10yr_change': 8.2,
                    'vix_change': 12.3,
                    'sp500_change': -0.8
                }

                summary = validator.get_validation_summary(validation_result)

                assert 'VALIDATED' in summary
                assert '0.75' in summary
                assert '3/4' in summary
