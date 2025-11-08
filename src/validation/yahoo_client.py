"""
Yahoo Finance client for fetching intraday market data (VIX, S&P 500).

Provides wrapper around yfinance library for FOMC statement impact analysis.
Handles intraday data with specific time windows (e.g., 30-min post-FOMC).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from pathlib import Path

import yfinance as yf
import pandas as pd
import pytz

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class YahooClient:
    """
    Client for fetching intraday market data from Yahoo Finance.

    Focuses on VIX (volatility index) and S&P 500 for market validation.
    Uses intraday data (5-min, 15-min, 30-min intervals) for precise timing.
    """

    # FOMC typically releases at 2:00 PM ET
    FOMC_RELEASE_HOUR = 14  # 2 PM
    FOMC_RELEASE_MINUTE = 0

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize Yahoo Finance client.

        Args:
            cache_dir: Directory for caching downloaded data. If None, uses config setting.
        """
        # Setup cache directory
        settings = get_settings()
        if cache_dir is None:
            cache_dir = Path(settings.get(
                'market_validation.storage.cache_dir',
                default='data/market_cache'
            ))
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Timezone for market data (US Eastern Time)
        self.et_tz = pytz.timezone('America/New_York')

        logger.info(f"YahooClient initialized with cache at {self.cache_dir}")

    def get_vix_data(
        self,
        date: str,
        interval: str = '5m',
        period_days: int = 5
    ) -> Optional[pd.DataFrame]:
        """
        Get VIX (volatility index) intraday data.

        Args:
            date: Date string in format 'YYYYMMDD' or 'YYYY-MM-DD'
            interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d')
            period_days: Number of days of data to fetch (to ensure we get the specific date)

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        try:
            symbol = '^VIX'
            return self._get_intraday_data(symbol, date, interval, period_days)
        except Exception as e:
            logger.error(f"Error fetching VIX data for {date}: {e}")
            return None

    def get_sp500_data(
        self,
        date: str,
        interval: str = '5m',
        period_days: int = 5
    ) -> Optional[pd.DataFrame]:
        """
        Get S&P 500 intraday data (using SPY ETF as proxy).

        Args:
            date: Date string in format 'YYYYMMDD' or 'YYYY-MM-DD'
            interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d')
            period_days: Number of days of data to fetch

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        try:
            symbol = 'SPY'  # S&P 500 ETF (more liquid than ^GSPC)
            return self._get_intraday_data(symbol, date, interval, period_days)
        except Exception as e:
            logger.error(f"Error fetching S&P 500 data for {date}: {e}")
            return None

    def calculate_vix_change(
        self,
        date: str,
        window_minutes: int = 30
    ) -> Optional[float]:
        """
        Calculate VIX percentage change in post-FOMC window.

        Args:
            date: FOMC statement release date (YYYYMMDD or YYYY-MM-DD)
            window_minutes: Time window after FOMC release (default: 30 minutes)

        Returns:
            Percentage change in VIX (e.g., 12.5 for 12.5% increase)
        """
        try:
            # Get intraday data
            vix_data = self.get_vix_data(date, interval='5m')
            if vix_data is None or vix_data.empty:
                logger.warning(f"No VIX data available for {date}")
                return None

            # Parse date and create FOMC release time (2:00 PM ET)
            date_obj = self._parse_date(date)
            release_time = self.et_tz.localize(
                datetime(date_obj.year, date_obj.month, date_obj.day,
                        self.FOMC_RELEASE_HOUR, self.FOMC_RELEASE_MINUTE)
            )

            # Get baseline (right before release)
            baseline_start = release_time - timedelta(minutes=15)
            baseline_end = release_time
            baseline_value = self._get_average_price(vix_data, baseline_start, baseline_end)

            if baseline_value is None:
                logger.warning(f"Could not establish VIX baseline for {date}")
                return None

            # Get post-release value
            post_start = release_time
            post_end = release_time + timedelta(minutes=window_minutes)
            post_value = self._get_max_price(vix_data, post_start, post_end)  # Use max for VIX spike

            if post_value is None:
                logger.warning(f"Could not get VIX post-release value for {date}")
                return None

            # Calculate percentage change
            pct_change = ((post_value - baseline_value) / baseline_value) * 100

            logger.info(
                f"VIX change on {date}: {baseline_value:.2f} → {post_value:.2f} "
                f"= {pct_change:+.2f}%"
            )

            return pct_change

        except Exception as e:
            logger.error(f"Error calculating VIX change for {date}: {e}")
            return None

    def calculate_sp500_change(
        self,
        date: str,
        window_minutes: int = 30
    ) -> Optional[float]:
        """
        Calculate S&P 500 percentage change in post-FOMC window.

        Args:
            date: FOMC statement release date (YYYYMMDD or YYYY-MM-DD)
            window_minutes: Time window after FOMC release (default: 30 minutes)

        Returns:
            Percentage change in S&P 500 (e.g., -1.5 for 1.5% decrease)
        """
        try:
            # Get intraday data
            sp_data = self.get_sp500_data(date, interval='5m')
            if sp_data is None or sp_data.empty:
                logger.warning(f"No S&P 500 data available for {date}")
                return None

            # Parse date and create FOMC release time
            date_obj = self._parse_date(date)
            release_time = self.et_tz.localize(
                datetime(date_obj.year, date_obj.month, date_obj.day,
                        self.FOMC_RELEASE_HOUR, self.FOMC_RELEASE_MINUTE)
            )

            # Get baseline (right before release)
            baseline_start = release_time - timedelta(minutes=15)
            baseline_end = release_time
            baseline_value = self._get_average_price(sp_data, baseline_start, baseline_end)

            if baseline_value is None:
                logger.warning(f"Could not establish S&P 500 baseline for {date}")
                return None

            # Get post-release value (average over window)
            post_start = release_time
            post_end = release_time + timedelta(minutes=window_minutes)
            post_value = self._get_average_price(sp_data, post_start, post_end)

            if post_value is None:
                logger.warning(f"Could not get S&P 500 post-release value for {date}")
                return None

            # Calculate percentage change
            pct_change = ((post_value - baseline_value) / baseline_value) * 100

            logger.info(
                f"S&P 500 change on {date}: {baseline_value:.2f} → {post_value:.2f} "
                f"= {pct_change:+.2f}%"
            )

            return pct_change

        except Exception as e:
            logger.error(f"Error calculating S&P 500 change for {date}: {e}")
            return None

    def get_all_market_data(self, date: str) -> Dict[str, Optional[float]]:
        """
        Get all market reaction data for a given date.

        Returns:
            Dictionary with keys: vix_change, sp500_change
        """
        return {
            'vix_change': self.calculate_vix_change(date),
            'sp500_change': self.calculate_sp500_change(date),
        }

    def _get_intraday_data(
        self,
        symbol: str,
        date: str,
        interval: str,
        period_days: int
    ) -> Optional[pd.DataFrame]:
        """Fetch intraday data from Yahoo Finance."""
        try:
            # Check cache first
            cached_data = self._get_from_cache(symbol, date, interval)
            if cached_data is not None:
                logger.debug(f"Cache hit for {symbol} on {date} ({interval})")
                return cached_data

            # Parse date
            date_obj = self._parse_date(date)

            # Calculate period
            start_date = date_obj - timedelta(days=period_days)
            end_date = date_obj + timedelta(days=1)

            logger.debug(f"Fetching {symbol} intraday data: {start_date} to {end_date}")

            # Download data
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval=interval
            )

            if data.empty:
                logger.warning(f"No data returned for {symbol} on {date}")
                return None

            # Filter for specific date
            date_str = date_obj.strftime('%Y-%m-%d')
            data_for_date = data[data.index.date == date_obj.date()]

            if data_for_date.empty:
                logger.warning(f"No {symbol} data for specific date {date}")
                return None

            # Cache the result
            self._save_to_cache(symbol, date, interval, data_for_date)

            logger.info(f"Fetched {len(data_for_date)} {interval} bars for {symbol} on {date}")
            return data_for_date

        except Exception as e:
            logger.error(f"Error fetching {symbol} data: {e}")
            return None

    def _get_average_price(
        self,
        data: pd.DataFrame,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[float]:
        """Get average price in time window."""
        try:
            # Filter data for time window
            mask = (data.index >= start_time) & (data.index <= end_time)
            window_data = data[mask]

            if window_data.empty:
                return None

            # Use Close prices
            avg_price = window_data['Close'].mean()
            return float(avg_price)

        except Exception as e:
            logger.error(f"Error calculating average price: {e}")
            return None

    def _get_max_price(
        self,
        data: pd.DataFrame,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[float]:
        """Get maximum price in time window (useful for VIX spikes)."""
        try:
            mask = (data.index >= start_time) & (data.index <= end_time)
            window_data = data[mask]

            if window_data.empty:
                return None

            max_price = window_data['High'].max()
            return float(max_price)

        except Exception as e:
            logger.error(f"Error calculating max price: {e}")
            return None

    def _parse_date(self, date: str) -> datetime:
        """Parse date string to datetime object."""
        if len(date) == 8:  # YYYYMMDD
            return datetime.strptime(date, '%Y%m%d')
        else:  # YYYY-MM-DD
            return datetime.strptime(date, '%Y-%m-%d')

    def _get_from_cache(
        self,
        symbol: str,
        date: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Retrieve data from cache if available."""
        try:
            cache_file = (
                self.cache_dir / f"{symbol.lower().replace('^', '')}"
                / f"{date}_{interval}.csv"
            )
            if cache_file.exists():
                data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                # Make index timezone-aware
                if data.index.tz is None:
                    data.index = data.index.tz_localize(self.et_tz)
                return data
        except Exception as e:
            logger.debug(f"Cache read error: {e}")
        return None

    def _save_to_cache(
        self,
        symbol: str,
        date: str,
        interval: str,
        data: pd.DataFrame
    ) -> None:
        """Save data to cache."""
        try:
            cache_subdir = self.cache_dir / f"{symbol.lower().replace('^', '')}"
            cache_subdir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_subdir / f"{date}_{interval}.csv"
            data.to_csv(cache_file)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
