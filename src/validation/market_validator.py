"""
Market Validator - Main orchestrator for market data validation.

Coordinates FRED and Yahoo Finance clients to validate language shifts
using market reactions (Treasury yields, VIX, S&P 500).
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from src.config.settings import get_settings
from src.validation.fred_client import FREDClient
from src.validation.yahoo_client import YahooClient
from src.validation.cache import MarketDataCache

logger = logging.getLogger(__name__)


class MarketValidator:
    """
    Validates language shift detections using market data reactions.

    Combines Treasury yield changes, VIX spikes, and S&P 500 movements
    to determine if a detected language shift had significant market impact.
    """

    def __init__(
        self,
        fred_client: Optional[FREDClient] = None,
        yahoo_client: Optional[YahooClient] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize market validator.

        Args:
            fred_client: FRED API client. If None, creates new instance.
            yahoo_client: Yahoo Finance client. If None, creates new instance.
            config: Override configuration. If None, uses config.yaml settings.
        """
        # Load configuration
        settings = get_settings()
        if config is None:
            config = settings.get('market_validation', default={})

        self.config = config
        self.enabled = config.get('enabled', True)

        if not self.enabled:
            logger.warning("Market validation is DISABLED in configuration")
            return

        # Initialize clients
        try:
            self.fred_client = fred_client or FREDClient()
            self.yahoo_client = yahoo_client or YahooClient()
            self.cache = MarketDataCache()
        except ValueError as e:
            logger.error(f"Failed to initialize market validator: {e}")
            self.enabled = False
            return

        # Load thresholds from config
        indicators_config = config.get('indicators', {})
        self.treasury_2yr_threshold = indicators_config.get('treasury_2yr', {}).get('threshold_bps', 5)
        self.treasury_10yr_threshold = indicators_config.get('treasury_10yr', {}).get('threshold_bps', 5)
        self.vix_threshold = indicators_config.get('vix', {}).get('threshold_pct', 10)
        self.sp500_threshold = indicators_config.get('sp500', {}).get('threshold_pct', 0.5)

        # Load weights
        self.treasury_2yr_weight = indicators_config.get('treasury_2yr', {}).get('weight', 0.20)
        self.treasury_10yr_weight = indicators_config.get('treasury_10yr', {}).get('weight', 0.20)
        self.vix_weight = indicators_config.get('vix', {}).get('weight', 0.30)
        self.sp500_weight = indicators_config.get('sp500', {}).get('weight', 0.30)

        # Load validation criteria
        validation_config = config.get('validation', {})
        self.min_score = validation_config.get('min_score', 0.6)
        self.min_indicators = validation_config.get('min_indicators', 2)

        logger.info("MarketValidator initialized successfully")
        logger.info(
            f"Thresholds: 2YR={self.treasury_2yr_threshold}bps, "
            f"10YR={self.treasury_10yr_threshold}bps, "
            f"VIX={self.vix_threshold}%, SP500={self.sp500_threshold}%"
        )
        logger.info(
            f"Validation criteria: min_score={self.min_score}, "
            f"min_indicators={self.min_indicators}"
        )

    def validate_shift(
        self,
        date: str,
        term: str,
        shift_type: str
    ) -> Dict:
        """
        Validate a detected language shift using market data.

        Args:
            date: FOMC statement date (YYYYMMDD or YYYY-MM-DD)
            term: Term that shifted (e.g., "transitory")
            shift_type: Type of shift ("emergence", "removal", "increase", "decrease")

        Returns:
            Dictionary with validation results:
            {
                'validated': bool,  # True if market validated
                'market_score': float,  # 0-1 score
                'indicators_triggered': int,  # Number of indicators that exceeded threshold
                'treasury_2yr_change': float or None,  # Basis points
                'treasury_10yr_change': float or None,  # Basis points
                'vix_change': float or None,  # Percentage
                'sp500_change': float or None,  # Percentage
                'signals': dict,  # Which indicators triggered (1) or not (0)
                'timestamp': str,  # When validation was performed
                'error': str or None  # Error message if validation failed
            }
        """
        if not self.enabled:
            return self._empty_result(error="Market validation disabled")

        logger.info(f"Validating shift: {shift_type} of '{term}' on {date}")

        try:
            # Fetch all market data
            treasury_data = self.fred_client.get_all_treasury_data(date)
            market_data = self.yahoo_client.get_all_market_data(date)

            # Extract values
            dgs2_change = treasury_data.get('dgs2_change')
            dgs10_change = treasury_data.get('dgs10_change')
            vix_change = market_data.get('vix_change')
            sp500_change = market_data.get('sp500_change')

            # Calculate signals (1 if threshold exceeded, 0 otherwise)
            signals = self._calculate_signals(
                dgs2_change, dgs10_change, vix_change, sp500_change
            )

            # Calculate weighted market score
            market_score = self._calculate_market_score(signals)

            # Count triggered indicators
            indicators_triggered = sum(signals.values())

            # Determine validation
            validated = (
                market_score >= self.min_score and
                indicators_triggered >= self.min_indicators
            )

            result = {
                'validated': validated,
                'market_score': round(market_score, 3),
                'indicators_triggered': indicators_triggered,
                'treasury_2yr_change': round(dgs2_change, 2) if dgs2_change is not None else None,
                'treasury_10yr_change': round(dgs10_change, 2) if dgs10_change is not None else None,
                'vix_change': round(vix_change, 2) if vix_change is not None else None,
                'sp500_change': round(sp500_change, 2) if sp500_change is not None else None,
                'signals': signals,
                'timestamp': datetime.now().isoformat(),
                'error': None
            }

            logger.info(
                f"Validation result: validated={validated}, score={market_score:.3f}, "
                f"triggered={indicators_triggered}/{len(signals)}"
            )

            return result

        except Exception as e:
            logger.error(f"Error validating shift on {date}: {e}")
            return self._empty_result(error=str(e))

    def determine_tier(
        self,
        statistical_confidence: str,
        market_validated: bool
    ) -> Tuple[int, str]:
        """
        Determine alert tier based on statistical confidence and market validation.

        Args:
            statistical_confidence: Original detector confidence ("high", "medium", "low")
            market_validated: Whether market data validated the shift

        Returns:
            Tuple of (tier_number, tier_name):
                (1, "tier_1"): Statistical + Market validated (highest quality)
                (2, "tier_2"): Statistical only, not market validated
                (3, "tier_3"): Low statistical confidence (informational)
        """
        if statistical_confidence == "low":
            return (3, "tier_3")

        if statistical_confidence in ["high", "medium"]:
            if market_validated:
                return (1, "tier_1")  # Best quality: both signals
            else:
                return (2, "tier_2")  # Statistical only

        # Fallback
        logger.warning(f"Unknown confidence level: {statistical_confidence}")
        return (3, "tier_3")

    def _calculate_signals(
        self,
        dgs2_change: Optional[float],
        dgs10_change: Optional[float],
        vix_change: Optional[float],
        sp500_change: Optional[float]
    ) -> Dict[str, int]:
        """
        Calculate binary signals for each indicator.

        Returns:
            Dictionary with keys: treasury_2yr, treasury_10yr, vix, sp500
            Values: 1 if threshold exceeded, 0 otherwise
        """
        signals = {}

        # Treasury 2-year (signal if absolute change exceeds threshold)
        if dgs2_change is not None:
            signals['treasury_2yr'] = 1 if abs(dgs2_change) >= self.treasury_2yr_threshold else 0
        else:
            signals['treasury_2yr'] = 0

        # Treasury 10-year
        if dgs10_change is not None:
            signals['treasury_10yr'] = 1 if abs(dgs10_change) >= self.treasury_10yr_threshold else 0
        else:
            signals['treasury_10yr'] = 0

        # VIX (signal if increase exceeds threshold, negative changes don't signal)
        if vix_change is not None:
            signals['vix'] = 1 if vix_change >= self.vix_threshold else 0
        else:
            signals['vix'] = 0

        # S&P 500 (signal if absolute change exceeds threshold)
        if sp500_change is not None:
            signals['sp500'] = 1 if abs(sp500_change) >= self.sp500_threshold else 0
        else:
            signals['sp500'] = 0

        return signals

    def _calculate_market_score(self, signals: Dict[str, int]) -> float:
        """
        Calculate weighted market validation score (0-1 scale).

        Args:
            signals: Dictionary of binary signals (0 or 1)

        Returns:
            Market score between 0.0 and 1.0
        """
        score = (
            signals.get('treasury_2yr', 0) * self.treasury_2yr_weight +
            signals.get('treasury_10yr', 0) * self.treasury_10yr_weight +
            signals.get('vix', 0) * self.vix_weight +
            signals.get('sp500', 0) * self.sp500_weight
        )

        return min(1.0, max(0.0, score))  # Clamp to [0, 1]

    def _empty_result(self, error: Optional[str] = None) -> Dict:
        """Return empty validation result (used when validation fails or is disabled)."""
        return {
            'validated': False,
            'market_score': 0.0,
            'indicators_triggered': 0,
            'treasury_2yr_change': None,
            'treasury_10yr_change': None,
            'vix_change': None,
            'sp500_change': None,
            'signals': {
                'treasury_2yr': 0,
                'treasury_10yr': 0,
                'vix': 0,
                'sp500': 0
            },
            'timestamp': datetime.now().isoformat(),
            'error': error
        }

    def get_validation_summary(self, validation_result: Dict) -> str:
        """
        Generate human-readable summary of validation result.

        Args:
            validation_result: Result dictionary from validate_shift()

        Returns:
            Summary string
        """
        if validation_result.get('error'):
            return f"Validation failed: {validation_result['error']}"

        validated = validation_result['validated']
        score = validation_result['market_score']
        triggered = validation_result['indicators_triggered']

        indicators = []
        if validation_result.get('treasury_2yr_change') is not None:
            indicators.append(f"2YR: {validation_result['treasury_2yr_change']:+.1f}bps")
        if validation_result.get('treasury_10yr_change') is not None:
            indicators.append(f"10YR: {validation_result['treasury_10yr_change']:+.1f}bps")
        if validation_result.get('vix_change') is not None:
            indicators.append(f"VIX: {validation_result['vix_change']:+.1f}%")
        if validation_result.get('sp500_change') is not None:
            indicators.append(f"SPY: {validation_result['sp500_change']:+.1f}%")

        indicators_str = ", ".join(indicators) if indicators else "no data"

        status = "VALIDATED" if validated else "NOT VALIDATED"
        return (
            f"{status} (score: {score:.2f}, {triggered}/4 indicators triggered) "
            f"[{indicators_str}]"
        )
