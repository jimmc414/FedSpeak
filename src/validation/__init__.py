"""
Market validation module for FedSpeak.

This module provides market data integration to validate language shift detections
using external market reactions (Treasury yields, VIX, S&P500).
"""

from src.validation.market_validator import MarketValidator
from src.validation.fred_client import FREDClient
from src.validation.yahoo_client import YahooClient
from src.validation.cache import MarketDataCache

__all__ = [
    'MarketValidator',
    'FREDClient',
    'YahooClient',
    'MarketDataCache',
]
