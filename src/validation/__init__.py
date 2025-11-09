"""
Validation module for FedSpeak.

This module provides external validation for language shift detections:
- Phase 5: Market data validation (Treasury yields, VIX, S&P500)
- Phase 6: Media coverage validation (GDELT, FinBERT sentiment)
"""

from src.validation.market_validator import MarketValidator
from src.validation.fred_client import FREDClient
from src.validation.yahoo_client import YahooClient
from src.validation.cache import MarketDataCache
from src.validation.media_validator import MediaValidator

__all__ = [
    'MarketValidator',
    'FREDClient',
    'YahooClient',
    'MarketDataCache',
    'MediaValidator',
]
