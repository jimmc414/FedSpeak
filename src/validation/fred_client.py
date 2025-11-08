"""
FRED (Federal Reserve Economic Data) API client for fetching Treasury yields.

Provides wrapper around fredapi library with error handling, caching, and
FedSpeak-specific integration.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

from fredapi import Fred
import pandas as pd

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class FREDClient:
    """
    Client for fetching economic data from FRED API.

    Focuses on Treasury yields (2-year and 10-year) for market validation.
    Uses daily data (FRED limitation - no intraday available).
    """

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize FRED client.

        Args:
            api_key: FRED API key. If None, reads from FRED_API_KEY environment variable.
            cache_dir: Directory for caching downloaded data. If None, uses config setting.
        """
        # Get API key
        if api_key is None:
            api_key = os.getenv('FRED_API_KEY')
            if not api_key:
                logger.error("FRED API key not found. Set FRED_API_KEY environment variable.")
                raise ValueError(
                    "FRED API key required. Get free key at "
                    "https://fred.stlouisfed.org/docs/api/api_key.html"
                )

        self.api_key = api_key
        self.fred = Fred(api_key=api_key)

        # Setup cache directory
        settings = get_settings()
        if cache_dir is None:
            cache_dir = Path(settings.get(
                'market_validation.storage.cache_dir',
                default='data/market_cache'
            ))
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"FREDClient initialized with cache at {self.cache_dir}")

    def get_treasury_yield(
        self,
        series_id: str,
        date: str,
        window_days: int = 7
    ) -> Optional[float]:
        """
        Get Treasury yield for a specific date.

        Args:
            series_id: FRED series ID (e.g., 'DGS2' for 2-year, 'DGS10' for 10-year)
            date: Date string in format 'YYYYMMDD' or 'YYYY-MM-DD'
            window_days: If exact date unavailable, search within this many days

        Returns:
            Yield value (as percentage) or None if not available
        """
        try:
            # Parse date
            if len(date) == 8:  # YYYYMMDD format
                date_obj = datetime.strptime(date, '%Y%m%d')
            else:  # YYYY-MM-DD format
                date_obj = datetime.strptime(date, '%Y-%m-%d')

            # Fetch data for date range (with window for weekends/holidays)
            start_date = date_obj - timedelta(days=window_days)
            end_date = date_obj + timedelta(days=1)

            logger.debug(f"Fetching {series_id} for {date} (window: {start_date} to {end_date})")

            # Try cache first
            cached_value = self._get_from_cache(series_id, date)
            if cached_value is not None:
                logger.debug(f"Cache hit for {series_id} on {date}: {cached_value}")
                return cached_value

            # Fetch from FRED API
            data = self.fred.get_series(
                series_id,
                observation_start=start_date.strftime('%Y-%m-%d'),
                observation_end=end_date.strftime('%Y-%m-%d')
            )

            if data.empty:
                logger.warning(f"No data found for {series_id} near {date}")
                return None

            # Find closest date
            closest_idx = (data.index - date_obj).abs().argmin()
            closest_date = data.index[closest_idx]
            value = data.iloc[closest_idx]

            # Check if closest date is within window
            if abs((closest_date - date_obj).days) > window_days:
                logger.warning(
                    f"Closest data for {series_id} is {closest_date}, "
                    f"which is {abs((closest_date - date_obj).days)} days from {date}"
                )
                return None

            # Cache the result
            self._save_to_cache(series_id, date, float(value))

            logger.info(f"Fetched {series_id} on {closest_date}: {value:.2f}%")
            return float(value)

        except Exception as e:
            logger.error(f"Error fetching {series_id} for {date}: {e}")
            return None

    def get_treasury_change(
        self,
        series_id: str,
        date: str,
        baseline_days: int = 1
    ) -> Optional[float]:
        """
        Get change in Treasury yield from previous trading day.

        Args:
            series_id: FRED series ID
            date: Date string in format 'YYYYMMDD' or 'YYYY-MM-DD'
            baseline_days: Number of days back to compare (default: 1 = previous day)

        Returns:
            Change in yield (basis points) or None if data unavailable
        """
        try:
            # Get current value
            current_value = self.get_treasury_yield(series_id, date)
            if current_value is None:
                return None

            # Parse date
            if len(date) == 8:
                date_obj = datetime.strptime(date, '%Y%m%d')
            else:
                date_obj = datetime.strptime(date, '%Y-%m-%d')

            # Get previous value
            prev_date_obj = date_obj - timedelta(days=baseline_days)
            prev_date = prev_date_obj.strftime('%Y%m%d')
            prev_value = self.get_treasury_yield(series_id, prev_date, window_days=7)

            if prev_value is None:
                logger.warning(f"Could not find baseline value for {series_id} on {prev_date}")
                return None

            # Calculate change in basis points
            change_bps = (current_value - prev_value) * 100  # Convert % to basis points

            logger.info(
                f"{series_id} change: {prev_value:.2f}% → {current_value:.2f}% "
                f"= {change_bps:+.1f} bps"
            )

            return change_bps

        except Exception as e:
            logger.error(f"Error calculating {series_id} change for {date}: {e}")
            return None

    def get_2yr_yield(self, date: str) -> Optional[float]:
        """Get 2-year Treasury yield for a specific date."""
        return self.get_treasury_yield('DGS2', date)

    def get_10yr_yield(self, date: str) -> Optional[float]:
        """Get 10-year Treasury yield for a specific date."""
        return self.get_treasury_yield('DGS10', date)

    def get_2yr_change(self, date: str, baseline_days: int = 1) -> Optional[float]:
        """Get 2-year Treasury yield change (basis points)."""
        return self.get_treasury_change('DGS2', date, baseline_days)

    def get_10yr_change(self, date: str, baseline_days: int = 1) -> Optional[float]:
        """Get 10-year Treasury yield change (basis points)."""
        return self.get_treasury_change('DGS10', date, baseline_days)

    def get_all_treasury_data(self, date: str) -> Dict[str, Optional[float]]:
        """
        Get all Treasury data for a given date.

        Returns:
            Dictionary with keys: dgs2, dgs10, dgs2_change, dgs10_change
        """
        return {
            'dgs2': self.get_2yr_yield(date),
            'dgs10': self.get_10yr_yield(date),
            'dgs2_change': self.get_2yr_change(date),
            'dgs10_change': self.get_10yr_change(date),
        }

    def _get_from_cache(self, series_id: str, date: str) -> Optional[float]:
        """Retrieve value from cache if available."""
        try:
            cache_file = self.cache_dir / f"{series_id.lower()}" / f"{date}.txt"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return float(f.read().strip())
        except Exception as e:
            logger.debug(f"Cache read error: {e}")
        return None

    def _save_to_cache(self, series_id: str, date: str, value: float) -> None:
        """Save value to cache."""
        try:
            cache_subdir = self.cache_dir / f"{series_id.lower()}"
            cache_subdir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_subdir / f"{date}.txt"
            with open(cache_file, 'w') as f:
                f.write(f"{value:.4f}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def download_historical_data(
        self,
        series_id: str,
        start_date: str = '2009-01-01',
        end_date: Optional[str] = None
    ) -> pd.Series:
        """
        Download historical data for backtesting.

        Args:
            series_id: FRED series ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            pandas Series with date index and values
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Downloading {series_id} historical data: {start_date} to {end_date}")

        try:
            data = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
            logger.info(f"Downloaded {len(data)} observations for {series_id}")
            return data

        except Exception as e:
            logger.error(f"Error downloading historical data for {series_id}: {e}")
            return pd.Series()
