"""
Validation module for FedSpeak.

This module provides external validation for language shift detections:
- Phase 5: Market data validation (Treasury yields, VIX, S&P500)
- Phase 6: Media coverage validation (GDELT, FinBERT sentiment)
"""

from .market_validator import MarketValidator
from .fred_client import FREDClient
from .yahoo_client import YahooClient
from .cache import MarketDataCache
from .media_validator import MediaValidator

__all__ = [
    'MarketValidator',
    'FREDClient',
    'YahooClient',
    'MarketDataCache',
    'MediaValidator',
]
